import logging

from telegram import Update
from telegram.ext import ContextTypes

from localization.utils import t

logger = logging.getLogger(__name__)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"❓ User {user.id} requested help")

    help_text = f"""
📖 {t('help_title', user=user)}

🎯 {t('help_usage', user=user)}:
1. {t('help_usage_text', user=user)}
2. Wait for processing (may take a few seconds)
3. Receive the downloaded video

📱 {t('help_platforms', user=user)}:

🔸 {t('help_instagram', user=user)}:
{t('help_instagram_examples', user=user)}

🔸 {t('help_tiktok', user=user)}:
{t('help_tiktok_examples', user=user)}

🔸 {t('help_youtube', user=user)}:
{t('help_youtube_examples', user=user)}

🔸 {t('help_likee', user=user)}:
{t('help_likee_examples', user=user)}

🔸 {t('help_facebook', user=user)}:
{t('help_facebook_examples', user=user)}

🔸 {t('help_rutube', user=user)}:
{t('help_rutube_examples', user=user)}

⚠️ {t('help_limitations', user=user)}:
{t('help_limitations_text', user=user)}

 👥 {t('help_groups', user=user)}:
 {t('help_groups_text', user=user)}

🆘 If you have problems:
• Make sure the link is correct
• Check that the account is public
• Try another link

💡 {t('help_commands', user=user)}:
{t('help_start', user=user)}
{t('help_help', user=user)}
{t('help_contact', user=user)}
    """

    await update.message.reply_text(help_text)
