"""
Переводы для ShortlyBot
"""

# Словари с переводами
TRANSLATIONS = {
    "ru": {
        # Команда /start
        "start_welcome": "Привет, {name}! 👋",
        "start_description": "Я бот для скачивания видео из социальных сетей!",
        "start_supported_platforms": "Поддерживаемые платформы:",
        "start_instagram": "• Instagram (посты, reels, IGTV)",
        "start_tiktok": "• TikTok (видео)",
        "start_youtube": "• YouTube Shorts (короткие видео)",
        "start_likee": "• Likee (короткие видео)",
        "start_facebook": "• Facebook Reels (короткие видео)",
        "start_rutube": "• RuTube (видео и shorts)",
        "start_usage": "Просто отправь мне ссылку на видео, и я скачаю его для тебя!",
        "start_help": "Используй /help для получения справки.",
        # Команда /help
        "help_title": "Справка по использованию бота:",
        "help_usage": "Как использовать:",
        "help_usage_text": "Отправь мне ссылку на видео из поддерживаемой платформы, и я скачаю его для тебя.",
        "help_platforms": "Поддерживаемые платформы:",
        "help_instagram": "Instagram:",
        "help_instagram_examples": "instagram.com/p/ABC123/\ninstagram.com/reel/XYZ789/\ninstagram.com/tv/DEF456/",
        "help_tiktok": "TikTok:",
        "help_tiktok_examples": "tiktok.com/@user/video/1234567890\nvm.tiktok.com/ABC123/",
        "help_youtube": "YouTube Shorts:",
        "help_youtube_examples": "youtube.com/shorts/ABC123\nyoutu.be/ABC123",
        "help_likee": "Likee:",
        "help_likee_examples": "likee.video/video/123456789\nlikee.com/@user/video/123456789",
        "help_facebook": "Facebook Reels:",
        "help_facebook_examples": "facebook.com/reel/123456789012345\nfb.watch/ABC123DEF/",
        "help_rutube": "RuTube:",
        "help_rutube_examples": "Видео: rutube.ru/video/abc123def456\nShorts: rutube.ru/shorts/cea63c15281278af170cdaec2115cf87\nEmbed: rutube.ru/play/embed/123456",
        "help_limitations": "Ограничения:",
        "help_limitations_text": "• Максимальная длительность: 5 минут\n• Максимальный размер: 50 МБ\n• Поддерживаются только короткие видео",
        "help_commands": "Команды:",
        "help_start": "/start - Начать работу с ботом",
        "help_help": "/help - Показать эту справку",
        # Сообщения об ошибках
        "error_unsupported_url": "❌ Неподдерживаемая ссылка. Пожалуйста, отправь ссылку из поддерживаемых платформ.",
        "error_download_failed": "❌ Не удалось скачать видео. Попробуй другую ссылку.",
        "error_video_not_found": "❌ Видео не найдено или недоступно.",
        "error_processing_timeout": "⏰ Превышено время ожидания. Попробуй еще раз.",
        "error_unknown": "❌ Произошла неизвестная ошибка. Попробуй еще раз.",
        "error_invalid_url": "❌ Некорректная ссылка. Проверь правильность URL.",
        # Сообщения о процессе
        "processing_video": "🎬 Обрабатываю видео...",
        "downloading_video": "⬇️ Скачиваю видео...",
        "sending_video": "📤 Отправляю видео...",
        "video_sent": "✅ Видео успешно отправлено!",
        # Статистика
        "stats_processing_time": "Время обработки: {time:.1f}с",
        "stats_video_size": "Размер: {size:.1f} МБ",
        # Общие
        "user": "Пользователь",
    },
    "en": {
        # /start command
        "start_welcome": "Hello, {name}! 👋",
        "start_description": "I'm a bot for downloading videos from social networks!",
        "start_supported_platforms": "Supported platforms:",
        "start_instagram": "• Instagram (posts, reels, IGTV)",
        "start_tiktok": "• TikTok (videos)",
        "start_youtube": "• YouTube Shorts (short videos)",
        "start_likee": "• Likee (short videos)",
        "start_facebook": "• Facebook Reels (short videos)",
        "start_rutube": "• RuTube (videos and shorts)",
        "start_usage": "Just send me a video link and I'll download it for you!",
        "start_help": "Use /help for help.",
        # /help command
        "help_title": "Bot usage help:",
        "help_usage": "How to use:",
        "help_usage_text": "Send me a link to a video from a supported platform and I'll download it for you.",
        "help_platforms": "Supported platforms:",
        "help_instagram": "Instagram:",
        "help_instagram_examples": "instagram.com/p/ABC123/\ninstagram.com/reel/XYZ789/\ninstagram.com/tv/DEF456/",
        "help_tiktok": "TikTok:",
        "help_tiktok_examples": "tiktok.com/@user/video/1234567890\nvm.tiktok.com/ABC123/",
        "help_youtube": "YouTube Shorts:",
        "help_youtube_examples": "youtube.com/shorts/ABC123\nyoutu.be/ABC123",
        "help_likee": "Likee:",
        "help_likee_examples": "likee.video/video/123456789\nlikee.com/@user/video/123456789",
        "help_facebook": "Facebook Reels:",
        "help_facebook_examples": "facebook.com/reel/123456789012345\nfb.watch/ABC123DEF/",
        "help_rutube": "RuTube:",
        "help_rutube_examples": "Videos: rutube.ru/video/abc123def456\nShorts: rutube.ru/shorts/cea63c15281278af170cdaec2115cf87\nEmbed: rutube.ru/play/embed/123456",
        "help_limitations": "Limitations:",
        "help_limitations_text": "• Maximum duration: 5 minutes\n• Maximum size: 50 MB\n• Only short videos are supported",
        "help_commands": "Commands:",
        "help_start": "/start - Start working with the bot",
        "help_help": "/help - Show this help",
        # Error messages
        "error_unsupported_url": "❌ Unsupported link. Please send a link from supported platforms.",
        "error_download_failed": "❌ Failed to download video. Try another link.",
        "error_video_not_found": "❌ Video not found or unavailable.",
        "error_processing_timeout": "⏰ Processing timeout. Please try again.",
        "error_unknown": "❌ An unknown error occurred. Please try again.",
        "error_invalid_url": "❌ Invalid link. Please check the URL format.",
        # Process messages
        "processing_video": "🎬 Processing video...",
        "downloading_video": "⬇️ Downloading video...",
        "sending_video": "📤 Sending video...",
        "video_sent": "✅ Video sent successfully!",
        # Statistics
        "stats_processing_time": "Processing time: {time:.1f}s",
        "stats_video_size": "Size: {size:.1f} MB",
        # General
        "user": "User",
    },
}

# Языки по умолчанию для разных кодов
DEFAULT_LANGUAGES = {
    "ru": "ru",  # Русский
    "uk": "ru",  # Украинский -> Русский
    "be": "ru",  # Белорусский -> Русский
    "kk": "ru",  # Казахский -> Русский
    "ky": "ru",  # Киргизский -> Русский
    "uz": "ru",  # Узбекский -> Русский
    "tg": "ru",  # Таджикский -> Русский
    "hy": "ru",  # Армянский -> Русский
    "az": "ru",  # Азербайджанский -> Русский
    "ka": "ru",  # Грузинский -> Русский
    "mn": "ru",  # Монгольский -> Русский
    "en": "en",  # Английский
    "es": "en",  # Испанский -> Английский
    "fr": "en",  # Французский -> Английский
    "de": "en",  # Немецкий -> Английский
    "it": "en",  # Итальянский -> Английский
    "pt": "en",  # Португальский -> Английский
    "nl": "en",  # Голландский -> Английский
    "sv": "en",  # Шведский -> Английский
    "no": "en",  # Норвежский -> Английский
    "da": "en",  # Датский -> Английский
    "fi": "en",  # Финский -> Английский
    "pl": "ru",  # Польский -> Русский
    "cs": "ru",  # Чешский -> Русский
    "sk": "ru",  # Словацкий -> Русский
    "hu": "en",  # Венгерский -> Английский
    "ro": "en",  # Румынский -> Английский
    "bg": "ru",  # Болгарский -> Русский
    "hr": "ru",  # Хорватский -> Русский
    "sr": "ru",  # Сербский -> Русский
    "sl": "ru",  # Словенский -> Русский
    "et": "en",  # Эстонский -> Английский
    "lv": "en",  # Латышский -> Английский
    "lt": "en",  # Литовский -> Английский
    "el": "en",  # Греческий -> Английский
    "tr": "en",  # Турецкий -> Английский
    "ar": "en",  # Арабский -> Английский
    "he": "en",  # Иврит -> Английский
    "fa": "en",  # Персидский -> Английский
    "ur": "en",  # Урду -> Английский
    "hi": "en",  # Хинди -> Английский
    "bn": "en",  # Бенгальский -> Английский
    "ta": "en",  # Тамильский -> Английский
    "te": "en",  # Телугу -> Английский
    "ml": "en",  # Малаялам -> Английский
    "kn": "en",  # Каннада -> Английский
    "gu": "en",  # Гуджарати -> Английский
    "pa": "en",  # Панджаби -> Английский
    "or": "en",  # Ория -> Английский
    "as": "en",  # Ассамский -> Английский
    "ne": "en",  # Непальский -> Английский
    "si": "en",  # Сингальский -> Английский
    "my": "en",  # Бирманский -> Английский
    "km": "en",  # Кхмерский -> Английский
    "lo": "en",  # Лаосский -> Английский
    "th": "en",  # Тайский -> Английский
    "vi": "en",  # Вьетнамский -> Английский
    "id": "en",  # Индонезийский -> Английский
    "ms": "en",  # Малайский -> Английский
    "tl": "en",  # Филиппинский -> Английский
    "ko": "en",  # Корейский -> Английский
    "ja": "en",  # Японский -> Английский
    "zh": "en",  # Китайский -> Английский
    "zh-cn": "en",  # Китайский (упрощенный) -> Английский
    "zh-tw": "en",  # Китайский (традиционный) -> Английский
}


def get_user_language(user_language_code: str = None) -> str:
    """
    Определяет язык пользователя на основе кода языка

    Args:
        user_language_code: Код языка пользователя из Telegram

    Returns:
        str: Код поддерживаемого языка ('ru' или 'en')
    """
    if not user_language_code:
        return "en"  # По умолчанию английский

    # Нормализуем код языка (берем только основную часть)
    lang_code = user_language_code.lower().split("-")[0].split("_")[0]

    return DEFAULT_LANGUAGES.get(lang_code, "en")


def get_text(key: str, language: str = "en", **kwargs) -> str:
    """
    Получает переведенный текст

    Args:
        key: Ключ перевода
        language: Код языка
        **kwargs: Параметры для форматирования строки

    Returns:
        str: Переведенный текст
    """
    if language not in TRANSLATIONS:
        language = "en"

    text = TRANSLATIONS[language].get(key, TRANSLATIONS["en"].get(key, key))

    try:
        return text.format(**kwargs)
    except (KeyError, ValueError):
        return text
