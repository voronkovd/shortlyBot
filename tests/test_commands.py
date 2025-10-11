import pytest
from unittest.mock import Mock, AsyncMock
from telegram import Update, User, Message
from telegram.ext import ContextTypes

from commands.start import start_command
from commands.help import help_command


class TestStartCommand:

    @pytest.fixture
    def mock_update(self):
        """Создает мок Update для тестирования"""
        update = Mock(spec=Update)
        update.effective_user = Mock(spec=User)
        update.effective_user.id = 12345
        update.effective_user.username = "test_user"
        update.effective_user.first_name = "Test"
        update.effective_user.language_code = "en"

        update.message = Mock(spec=Message)
        update.message.reply_text = AsyncMock()

        return update

    @pytest.fixture
    def mock_context(self):
        """Создает мок Context для тестирования"""
        return Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_start_command_success(self, mock_update, mock_context):
        """Тест успешного выполнения команды /start"""
        await start_command(mock_update, mock_context)

        # Проверяем, что reply_text был вызван
        mock_update.message.reply_text.assert_called_once()

        # Проверяем содержимое сообщения
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Hello, Test!" in call_args
        assert "Instagram" in call_args
        assert "TikTok" in call_args
        assert "YouTube" in call_args
        assert "Likee" in call_args
        assert "Facebook" in call_args
        assert "RuTube" in call_args

    @pytest.mark.asyncio
    async def test_start_command_no_first_name(self, mock_update, mock_context):
        """Тест команды /start без имени пользователя"""
        mock_update.effective_user.first_name = None
        mock_update.effective_user.language_code = "en"

        await start_command(mock_update, mock_context)

        # Проверяем, что reply_text был вызван
        mock_update.message.reply_text.assert_called_once()

        # Проверяем, что сообщение содержит приветствие
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Hello," in call_args


class TestHelpCommand:

    @pytest.fixture
    def mock_update(self):
        """Создает мок Update для тестирования"""
        update = Mock(spec=Update)
        update.effective_user = Mock(spec=User)
        update.effective_user.id = 12345
        update.effective_user.username = "test_user"
        update.effective_user.language_code = "en"

        update.message = Mock(spec=Message)
        update.message.reply_text = AsyncMock()

        return update

    @pytest.fixture
    def mock_context(self):
        """Создает мок Context для тестирования"""
        return Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_help_command_success(self, mock_update, mock_context):
        """Тест успешного выполнения команды /help"""
        await help_command(mock_update, mock_context)

        # Проверяем, что reply_text был вызван
        mock_update.message.reply_text.assert_called_once()

        # Проверяем содержимое сообщения
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "Bot usage help" in call_args
        assert "Instagram" in call_args
        assert "TikTok" in call_args
        assert "YouTube" in call_args
        assert "Likee" in call_args
        assert "Facebook" in call_args
        assert "RuTube" in call_args
        assert "/start" in call_args
        assert "/help" in call_args

    @pytest.mark.asyncio
    async def test_help_command_contains_platforms(self, mock_update, mock_context):
        """Тест, что команда /help содержит все поддерживаемые платформы"""
        await help_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args[0][0]

        # Проверяем наличие всех платформ
        platforms = ["Instagram", "TikTok", "YouTube", "Likee", "Facebook", "RuTube"]

        for platform in platforms:
            assert platform in call_args, f"Platform {platform} not found in help text"

    @pytest.mark.asyncio
    async def test_help_command_contains_commands(self, mock_update, mock_context):
        """Тест, что команда /help содержит все команды"""
        await help_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args[0][0]

        # Проверяем наличие команд
        commands = ["/start", "/help"]

        for command in commands:
            assert command in call_args, f"Command {command} not found in help text"

    @pytest.mark.asyncio
    async def test_help_command_contains_limitations(self, mock_update, mock_context):
        """Тест, что команда /help содержит ограничения"""
        await help_command(mock_update, mock_context)

        call_args = mock_update.message.reply_text.call_args[0][0]

        # Проверяем наличие раздела ограничений
        assert "Limitations" in call_args
        assert "5 minutes" in call_args
        assert "50 MB" in call_args
