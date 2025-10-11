import logging

from telegram import Update
from telegram.ext import ContextTypes

from localization.utils import t

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"👤 User {user.id} (@{user.username}) started the bot")

    name = user.first_name if user.first_name else t("user", user=user)

    welcome_text = f"""
🎬 {t('start_welcome', user=user, name=name)}

{t('start_description', user=user)}

📱 {t('start_supported_platforms', user=user)}:
{t('start_instagram', user=user)}
{t('start_tiktok', user=user)}
{t('start_youtube', user=user)}
{t('start_likee', user=user)}
{t('start_facebook', user=user)}
{t('start_rutube', user=user)}

🔗 {t('start_usage', user=user)}

❓ {t('start_help', user=user)}
    """

    await update.message.reply_text(welcome_text)
