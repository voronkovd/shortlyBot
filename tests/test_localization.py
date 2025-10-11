"""
Тесты для системы локализации
"""

from unittest.mock import Mock

from localization.translations import DEFAULT_LANGUAGES, get_text, get_user_language
from localization.utils import get_user_lang, t


class TestTranslations:
    """Тесты для модуля translations"""

    def test_get_user_language_russian(self):
        """Тест определения русского языка"""
        assert get_user_language("ru") == "ru"
        assert get_user_language("uk") == "ru"  # Украинский -> Русский
        assert get_user_language("be") == "ru"  # Белорусский -> Русский
        assert get_user_language("kk") == "ru"  # Казахский -> Русский

    def test_get_user_language_english(self):
        """Тест определения английского языка"""
        assert get_user_language("en") == "en"
        assert get_user_language("es") == "en"  # Испанский -> Английский
        assert get_user_language("fr") == "en"  # Французский -> Английский
        assert get_user_language("de") == "en"  # Немецкий -> Английский

    def test_get_user_language_unknown(self):
        """Тест неизвестного языка"""
        assert get_user_language("unknown") == "en"
        assert get_user_language("xyz") == "en"
        assert get_user_language(None) == "en"
        assert get_user_language("") == "en"

    def test_get_user_language_with_region(self):
        """Тест языка с регионом"""
        assert get_user_language("ru-RU") == "ru"
        assert get_user_language("en-US") == "en"
        assert get_user_language("uk-UA") == "ru"
        assert get_user_language("es-ES") == "en"

    def test_get_text_russian(self):
        """Тест получения русского текста"""
        assert get_text("start_welcome", "ru", name="Тест") == "Привет, Тест! 👋"
        assert (
            get_text("start_description", "ru")
            == "Я бот для скачивания видео из социальных сетей!"
        )
        assert (
            get_text("error_unknown", "ru")
            == "❌ Произошла неизвестная ошибка. Попробуй еще раз."
        )

    def test_get_text_english(self):
        """Тест получения английского текста"""
        assert get_text("start_welcome", "en", name="Test") == "Hello, Test! 👋"
        assert (
            get_text("start_description", "en")
            == "I'm a bot for downloading videos from social networks!"
        )
        assert (
            get_text("error_unknown", "en")
            == "❌ An unknown error occurred. Please try again."
        )

    def test_get_text_missing_key(self):
        """Тест отсутствующего ключа"""
        assert get_text("nonexistent_key", "ru") == "nonexistent_key"
        assert get_text("nonexistent_key", "en") == "nonexistent_key"

    def test_get_text_formatting(self):
        """Тест форматирования строк"""
        assert get_text("start_welcome", "ru", name="Алексей") == "Привет, Алексей! 👋"
        assert get_text("start_welcome", "en", name="John") == "Hello, John! 👋"

    def test_get_text_invalid_language(self):
        """Тест неверного языка"""
        assert get_text("start_welcome", "invalid", name="Test") == "Hello, Test! 👋"
        assert get_text("start_welcome", "xyz", name="Test") == "Hello, Test! 👋"


class TestUtils:
    """Тесты для модуля utils"""

    def test_get_user_lang_with_language_code(self):
        """Тест получения языка пользователя с кодом языка"""
        user = Mock()
        user.language_code = "ru"
        assert get_user_lang(user) == "ru"

        user.language_code = "en"
        assert get_user_lang(user) == "en"

        user.language_code = "uk"
        assert get_user_lang(user) == "ru"

    def test_get_user_lang_without_language_code(self):
        """Тест получения языка пользователя без кода языка"""
        user = Mock()
        user.language_code = None
        assert get_user_lang(user) == "en"

        user = None
        assert get_user_lang(user) == "en"

    def test_t_function_with_user(self):
        """Тест функции t с пользователем"""
        user = Mock()
        user.language_code = "ru"

        assert t("start_welcome", user=user, name="Тест") == "Привет, Тест! 👋"
        assert (
            t("error_unknown", user=user)
            == "❌ Произошла неизвестная ошибка. Попробуй еще раз."
        )

    def test_t_function_with_language(self):
        """Тест функции t с явным языком"""
        user = Mock()
        user.language_code = "ru"

        # Явный язык имеет приоритет
        assert (
            t("start_welcome", user=user, language="en", name="Test")
            == "Hello, Test! 👋"
        )
        assert (
            t("start_welcome", user=user, language="ru", name="Тест")
            == "Привет, Тест! 👋"
        )

    def test_t_function_without_user(self):
        """Тест функции t без пользователя"""
        assert t("start_welcome", name="Test") == "Hello, Test! 👋"
        assert t("error_unknown") == "❌ An unknown error occurred. Please try again."

    def test_t_function_formatting(self):
        """Тест форматирования в функции t"""
        user = Mock()
        user.language_code = "ru"

        assert t("start_welcome", user=user, name="Алексей") == "Привет, Алексей! 👋"
        assert (
            t("stats_processing_time", user=user, time=5.5) == "Время обработки: 5.5с"
        )


class TestLanguageMapping:
    """Тесты для маппинга языков"""

    def test_all_supported_languages_mapped(self):
        """Тест что все поддерживаемые языки имеют маппинг"""
        for lang_code in DEFAULT_LANGUAGES:
            assert DEFAULT_LANGUAGES[lang_code] in ["ru", "en"]

    def test_slavic_languages_to_russian(self):
        """Тест что славянские языки маппятся на русский"""
        slavic_languages = ["ru", "uk", "be", "bg", "hr", "sr", "sk", "cs", "pl"]
        for lang in slavic_languages:
            if lang in DEFAULT_LANGUAGES:
                assert DEFAULT_LANGUAGES[lang] == "ru"

    def test_romance_languages_to_english(self):
        """Тест что романские языки маппятся на английский"""
        romance_languages = ["es", "fr", "it", "pt", "ro"]
        for lang in romance_languages:
            if lang in DEFAULT_LANGUAGES:
                assert DEFAULT_LANGUAGES[lang] == "en"

    def test_germanic_languages_to_english(self):
        """Тест что германские языки маппятся на английский"""
        germanic_languages = ["en", "de", "nl", "sv", "no", "da"]
        for lang in germanic_languages:
            if lang in DEFAULT_LANGUAGES:
                assert DEFAULT_LANGUAGES[lang] == "en"
