import logging

from telegram import Update
from telegram.ext import ContextTypes

from localization.utils import t

logger = logging.getLogger(__name__)


async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"📧 User {user.id} requested contact information")

    contact_text = f"""
{t('contact_title', user=user)}

🌐 {t('contact_website', user=user)}: https://shortlybot.ru

{t('contact_description', user=user)}
    """

    await update.message.reply_text(contact_text)
