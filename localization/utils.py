"""
Утилиты для работы с локализацией
"""

from typing import Optional

from telegram import User

from .translations import get_text, get_user_language


def get_user_lang(user: Optional[User]) -> str:
    """
    Получает язык пользователя из объекта User

    Args:
        user: Объект пользователя Telegram

    Returns:
        str: Код языка ('ru' или 'en')
    """
    if not user:
        return "en"

    return get_user_language(user.language_code)


def t(
    key: str, user: Optional[User] = None, language: Optional[str] = None, **kwargs
) -> str:
    """
    Получает переведенный текст для пользователя

    Args:
        key: Ключ перевода
        user: Объект пользователя Telegram (для определения языка)
        language: Явно указанный язык (приоритет над user)
        **kwargs: Параметры для форматирования строки

    Returns:
        str: Переведенный текст
    """
    if language:
        lang = language
    elif user:
        lang = get_user_lang(user)
    else:
        lang = "en"

    return get_text(key, lang, **kwargs)
