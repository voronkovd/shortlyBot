#!/usr/bin/env python3
import asyncio
import logging
import os
import time

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from analytics.stats_collector import stats_collector
from commands.help import help_command
from commands.start import start_command
from handlers.downloader import Downloader
from localization.utils import t

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables")

downloader = Downloader()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    message_text = update.message.text

    logger.info(
        f"📨 Received message from user {user.id} (@{user.username}): {message_text}"
    )

    # Отслеживаем запрос пользователя
    stats_collector.track_user_request(user.id, user.username, "unknown")

    processing_msg = await update.message.reply_text(t("processing_video", user=user))

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
                await processing_msg.edit_text(t("error_video_not_found", user=user))
                return

            processing_time = time.time() - start_time
            logger.info(
                f"Video successfully downloaded from {platform} for user {user.id}, size: {len(video_data)} bytes"
            )

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

            # Удаляем исходное сообщение с ссылкой после успешной отправки видео
            try:
                await update.message.delete()
                logger.info(f"Original message deleted for user {user.id}")
            except Exception as delete_error:
                logger.warning(
                    f"Failed to delete original message for user {user.id}: {delete_error}"
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
        await processing_msg.edit_text(t("error_processing_timeout", user=user))
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error downloading video for user {user.id}: {e}")
        stats_collector.track_download_failure(
            user.id, user.username, "unknown", str(e), processing_time
        )
        await processing_msg.edit_text(t("error_unknown", user=user))


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Error processing update: {context.error}")


def main() -> None:
    logger.info("Starting Telegram Video Downloader Bot")

    # Отслеживаем запуск бота
    stats_collector.track_bot_start()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
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
