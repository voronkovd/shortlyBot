#!/usr/bin/env python3
import asyncio
import logging
import os
import time

from telegram import Chat, Update
from telegram.ext import (
    Application,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from analytics.stats_collector import stats_collector
from commands.contact import contact_command
from commands.help import help_command
from commands.start import start_command
from handlers.downloader import Downloader
from localization.utils import t


def setup_logging() -> None:
    # Читаем уровень из окружения, по умолчанию — ERROR (т.е. только ошибки и выше)
    level_name = os.getenv("LOG_LEVEL", "ERROR").upper()
    level = getattr(logging, level_name, logging.ERROR)

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=level,
    )

    # Урезаем шум от сторонних библиотек
    for noisy in (
        "httpx",  # используется python-telegram-bot
        "telegram",  # внутренние логи PTB
        "urllib3",
        "asyncio",
        "yt_dlp",
        "pika",
    ):
        logging.getLogger(noisy).setLevel(
            max(level, logging.ERROR if level < logging.ERROR else level)
        )


setup_logging()
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables")

downloader = Downloader()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    chat = update.effective_chat
    message_text = update.message.text

    # Определяем, является ли чат группой или супергруппой
    is_group = chat.type in (Chat.GROUP, Chat.SUPERGROUP)

    logger.info(
        f"📨 Received message from user {user.id} (@{user.username}) in {'group' if is_group else 'private'} chat: {message_text}"
    )

    # Определяем платформу из URL
    platform = "unknown"
    downloader_provider = downloader.get_downloader(message_text)
    if downloader_provider:
        platform = getattr(downloader_provider, "platform", "unknown")
        # Если platform пустая строка, используем fallback
        if not platform:
            platform = (
                downloader_provider.__class__.__name__.replace("Provider", "").lower()
                or "unknown"
            )

    # Отслеживаем запрос только в личных чатах
    if not is_group:
        stats_collector.track_user_request(user.id, user.username, platform)

    # В группах не показываем служебные сообщения
    processing_msg = None
    if not is_group:
        processing_msg = await update.message.reply_text(
            t("processing_video", user=user)
        )

    # Считаем группу «подписчиком» при любой активности
    if is_group:
        try:
            stats_collector.track_group_message(chat.id, chat.title or "", chat.type)
        except Exception:
            pass

    try:
        # Общий таймаут на весь процесс: 5 минут
        start_time = time.time()

        async def process_video():
            video_data, caption, platform = downloader.download_video(message_text)

            if not video_data:
                processing_time = time.time() - start_time
                stats_collector.track_download_failure(
                    user.id,
                    user.username,
                    platform or "unknown",
                    "Video not found or unavailable",
                    processing_time,
                )
                # В группах не показываем ошибки
                if not is_group and processing_msg:
                    await processing_msg.edit_text(
                        t("error_video_not_found", user=user)
                    )
                return

            processing_time = time.time() - start_time
            logger.info(
                f"Video successfully downloaded from {platform} for user {user.id}, size: {len(video_data)} bytes"
            )

            # В группах не показываем сообщение "Отправляю видео..."
            if not is_group and processing_msg:
                await processing_msg.edit_text(t("sending_video", user=user))

            if caption and len(caption) > 1024:
                caption = caption[:1021] + "..."

            filename = f"{platform}_video.mp4"

            await update.message.reply_video(
                video=video_data,
                caption=caption,
                filename=filename,
                read_timeout=120,  # 2 минуты на чтение
                write_timeout=120,  # 2 минуты на запись
                connect_timeout=30,  # 30 секунд на подключение
                pool_timeout=30,  # 30 секунд на получение соединения из пула
            )

            # Отслеживаем успешное скачивание
            stats_collector.track_download_success(
                user.id, user.username, platform, len(video_data), processing_time
            )

            # Удаляем сообщения только в личных чатах
            if not is_group:
                try:
                    # Удаляем исходное сообщение с ссылкой
                    await update.message.delete()
                    logger.info(f"Original message deleted for user {user.id}")

                    # Удаляем сообщение "Отправляю видео..."
                    if processing_msg:
                        await processing_msg.delete()
                        logger.info(f"Processing message deleted for user {user.id}")
                except Exception as delete_error:
                    logger.warning(
                        f"Failed to delete messages for user {user.id}: {delete_error}"
                    )

            logger.info(f"Video successfully sent to user {user.id}")

        # Выполняем с общим таймаутом 5 минут
        await asyncio.wait_for(process_video(), timeout=300)

    except asyncio.TimeoutError:
        processing_time = time.time() - start_time
        logger.error(f"Timeout processing video for user {user.id}")
        stats_collector.track_download_failure(
            user.id, user.username, "unknown", "Processing timeout", processing_time
        )
        # В группах не показываем ошибки
        if not is_group and processing_msg:
            await processing_msg.edit_text(t("error_processing_timeout", user=user))
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error downloading video for user {user.id}: {e}")
        stats_collector.track_download_failure(
            user.id, user.username, "unknown", str(e), processing_time
        )
        # В группах не показываем ошибки
        if not is_group and processing_msg:
            await processing_msg.edit_text(t("error_unknown", user=user))


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Error processing update: {context.error}")


async def handle_my_chat_member(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        my = update.my_chat_member
        if not my:
            return
        chat = my.chat
        # Бот добавлен или стал админом
        new_status = my.new_chat_member.status
        old_status = my.old_chat_member.status if my.old_chat_member else None
        if new_status in ("member", "administrator") and (
            old_status in ("left", "kicked", "restricted", None)
        ):
            if chat.type in (Chat.GROUP, Chat.SUPERGROUP):
                stats_collector.track_group_added(chat.id, chat.title or "", chat.type)
    except Exception as e:
        logger.warning(f"Failed to process my_chat_member: {e}")


def main() -> None:
    logger.info("Starting Telegram Video Downloader Bot")

    # Отслеживаем запуск бота
    stats_collector.track_bot_start()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("contact", contact_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.add_handler(
        ChatMemberHandler(handle_my_chat_member, ChatMemberHandler.MY_CHAT_MEMBER)
    )
    application.add_error_handler(error_handler)

    logger.info("Bot started and waiting for messages...")

    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
    finally:
        # Отслеживаем остановку бота
        stats_collector.track_bot_stop()


if __name__ == "__main__":
    main()
