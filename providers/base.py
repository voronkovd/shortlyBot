import glob
import logging
import os
import re
import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Union

import yt_dlp

logger = logging.getLogger(__name__)

KindId = Tuple[str, str]


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def compress_to_target(
    inp: str,
    outp: str,
    duration_s: float,
    target_bytes: int,
    max_height: int = 1080,
    audio_kbps: int = 128,
) -> None:
    """
    Сжимает видео до целевого размера (≈ target_bytes) двухпроходным H.264.
    Ставит ограничение по высоте (max_height), сохраняя пропорции.
    """
    if duration_s <= 0:
        raise RuntimeError("Unknown or zero duration; cannot compute target bitrate")

    overhead_bytes = 512 * 1024  # запас под контейнер/погрешность
    total_bits = max((target_bytes - overhead_bytes), int(target_bytes * 0.95)) * 8
    # Аудио фиксированно (можно сделать динамическим)
    a_bps = audio_kbps * 1000
    # Целевой общий битрейт
    total_bps = max(int(total_bits / duration_s), a_bps + 64_000)
    # Видео битрейт = общий - аудио
    v_bps = max(total_bps - a_bps, 128_000)  # не падаем ниже разумного минимума

    v_kbps = v_bps // 1000
    a_kbps = a_bps // 1000

    scale_filter = f"scale=-2:'min({max_height},ih)'"

    log_prefix = outp + ".2pass"
    # pass 1
    cmd1 = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-hide_banner",
        "-i",
        inp,
        "-vf",
        scale_filter,
        "-c:v",
        "libx264",
        "-b:v",
        f"{v_kbps}k",
        "-maxrate",
        f"{v_kbps}k",
        "-bufsize",
        f"{max(v_kbps*2, 500)}k",
        "-preset",
        "medium",
        "-tune",
        "fastdecode",
        "-pass",
        "1",
        "-passlogfile",
        log_prefix,
        "-an",
        "-f",
        "mp4",  # пишем в «пустоту», но формат задаём
        os.devnull,
    ]
    # pass 2
    cmd2 = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-hide_banner",
        "-i",
        inp,
        "-vf",
        scale_filter,
        "-c:v",
        "libx264",
        "-b:v",
        f"{v_kbps}k",
        "-maxrate",
        f"{v_kbps}k",
        "-bufsize",
        f"{max(v_kbps*2, 500)}k",
        "-preset",
        "medium",
        "-tune",
        "fastdecode",
        "-pass",
        "2",
        "-passlogfile",
        log_prefix,
        "-movflags",
        "+faststart",
        "-c:a",
        "aac",
        "-b:a",
        f"{a_kbps}k",
        outp,
    ]

    logger.info(
        f"Re-encoding target ≈ {human(target_bytes)} "
        f"(total ~{total_bps/1000:.0f} kbps; video ~{v_kbps} kbps, audio {a_kbps} kbps)"
    )

    try:
        subprocess.run(cmd1, check=True)
        subprocess.run(cmd2, check=True)
    finally:
        # Удаляем пасс-логи
        for ext in (".log", ".mbtree"):
            p = log_prefix + ext
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


class BaseProvider(ABC):
    PATTERNS: List[Tuple[str, str]] = []
    platform: str = ""

    def extract_id(self, url: str) -> Optional[KindId]:
        clean = url.split("?", 1)[0].split("#", 1)[0]
        for kind, pattern in self.PATTERNS:
            m = re.search(pattern, clean, flags=re.IGNORECASE)
            if m:
                return kind, m.group(1)
        return None

    @abstractmethod
    def is_valid_url(self, url: str) -> bool: ...

    @abstractmethod
    def _build_url(self, kind: str, ident: str) -> str: ...

    def _yt_opts(self, temp_dir: str) -> Dict:
        opts = {
            "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
            "format": "bv*[ext=mp4][vcodec=h264]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
            "merge_output_format": "mp4",
            "postprocessors": [
                {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"},
            ],
            "postprocessor_args": {
                "ffmpeg_o": ["-movflags", "+faststart"],
            },
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "writethumbnail": False,
            "writeinfojson": False,
            "noplaylist": True,
            "retries": 5,
            "fragment_retries": 5,
            "skip_unavailable_fragments": True,
            "concurrent_fragment_downloads": 1,
            "socket_timeout": 60,
            "windowsfilenames": True,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
            },
            "compat_opts": ["no-keep-subs", "no-attach-info-json"],
            "prefer_free_formats": False,
        }

        cookie_src = os.getenv("YTDLP_COOKIES_FILE_RUNTIME") or os.getenv(
            "YTDLP_COOKIES_FILE"
        )
        if cookie_src and os.path.exists(cookie_src):
            try:
                cookie_dst = os.path.join(temp_dir, "yt_cookies.txt")
                shutil.copyfile(cookie_src, cookie_dst)
                os.chmod(cookie_dst, 0o600)
                opts["cookiefile"] = cookie_dst
            except Exception as e:
                logger.warning(f"Cannot prepare cookiefile: {e}")

        max_h = int(os.getenv("MAX_HEIGHT", "1080"))
        opts["format_sort"] = [
            f"res:{max_h}",
            "codec:h264",
            "ext:mp4",
            "fps",
            "vbr",
            "abr",
        ]
        return opts

    def download_video(
        self, ref: Union[str, KindId]
    ) -> Tuple[Optional[bytes], Optional[str]]:
        if isinstance(ref, tuple):
            kind, ident = ref
        else:
            kind, ident = "post", ref

        platform_name = (
            self.platform or self.__class__.__name__.replace("Downloader", "").lower()
        )
        logger.info(f"🔍 Starting {platform_name} {kind} download for ID: {ident}")

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                ydl_opts = self._yt_opts(temp_dir)
                url = self._build_url(kind, ident)
                logger.info(f"Downloading via yt-dlp: {url}")

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        raise RuntimeError("Failed to get video information")
                    duration = float(info.get("duration") or 0.0)
                    logger.info(f"Title: {info.get('title')!r}, duration: {duration}")

                    try:
                        ydl.download([url])
                    except Exception as format_error:
                        logger.warning(
                            f"Format error: {format_error} → fallback to 'best'"
                        )
                        ydl_opts["format"] = "best"
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                            ydl2.download([url])

                files = []
                for ext in ("mp4", "webm", "mkv", "mov"):
                    files.extend(glob.glob(os.path.join(temp_dir, f"*.{ext}")))
                if not files:
                    raise RuntimeError("Video file not found after download")

                video_file = max(files, key=lambda p: os.path.getsize(p))
                size = os.path.getsize(video_file)
                logger.info(
                    f"📁 Selected file: {os.path.basename(video_file)} ({human(size)})"
                )

                # --- условное сжатие ---
                max_size_mb = int(os.getenv("MAX_SIZE_MB", "50"))
                target_bytes = max_size_mb * 1024 * 1024
                max_height = int(os.getenv("MAX_HEIGHT", "1080"))

                if size > target_bytes:
                    logger.info(f"File exceeds {max_size_mb} MB → compressing…")
                    outp = os.path.join(temp_dir, "compressed.mp4")
                    compress_to_target(
                        inp=video_file,
                        outp=outp,
                        duration_s=duration,
                        target_bytes=target_bytes,
                        max_height=max_height,
                        audio_kbps=int(os.getenv("AUDIO_KBPS", "128")),
                    )
                    final_file = outp
                else:
                    final_file = video_file

                with open(final_file, "rb") as f:
                    data = f.read()

                final_size = len(data)
                logger.info(f"✅ Final size: {human(final_size)}")

                # Формируем caption с атрибуцией
                title = info.get("title") or ""
                description = info.get("description") or ""
                uploader = info.get("uploader") or info.get("channel") or ""
                uploader_id = info.get("uploader_id") or info.get("channel_id") or ""

                # Создаем атрибуцию
                attribution = ""
                if uploader:
                    # Используем uploader_id если есть, иначе uploader
                    username = uploader_id if uploader_id else uploader
                    # Убираем лишние символы и приводим к нижнему регистру для @
                    username = re.sub(r"[^\w\-_.]", "", username.lower())
                    if username:
                        attribution = f"Video by @{username}"

                # Объединяем title, description и атрибуцию
                caption_parts = []
                if title:
                    caption_parts.append(title)
                if description and description != title:
                    # Добавляем описание только если оно отличается от заголовка
                    caption_parts.append(description)
                if attribution:
                    caption_parts.append(attribution)

                caption = "\n\n".join(caption_parts)[:1024]

                if caption:
                    logger.info(f"Caption preview: {caption[:80]}...")
                    if attribution:
                        logger.info(f"Video attribution: {attribution}")

                return data, caption

            except Exception as e:
                logger.error(f"yt-dlp error: {e}")
                raise
