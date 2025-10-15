from typing import Optional

from telegram import User

from .translations import get_text, get_user_language


def get_user_lang(user: Optional[User]) -> str:
    if not user:
        return "en"

    return get_user_language(user.language_code)


def t(
    key: str, user: Optional[User] = None, language: Optional[str] = None, **kwargs
) -> str:
    if language:
        lang = language
    elif user:
        lang = get_user_lang(user)
    else:
        lang = "en"

    return get_text(key, lang, **kwargs)
