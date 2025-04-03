import pytest
from aiogram import Bot, Dispatcher
from aiogram.types import Message, User, Chat
from aiogram.filters import Command
import os
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import inspect

# Добавляем корневую директорию проекта в PYTHONPATH для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем обработчики сообщений из бота
import bot  # Сначала импортируем весь модуль
from bot import send_welcome, get_status, list_monitors, list_incidents, is_authorized

# Создаем фикстуры для тестирования Telegram бота
@pytest.fixture
def mock_message():
    """Создает мок сообщения для тестирования обработчиков"""
    message = AsyncMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123456789  # Тестовый ID пользователя
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 123456789  # Тестовый ID чата
    message.answer = AsyncMock(return_value=None)
    return message

@pytest.fixture
def mock_allowed_user():
    """Создает мок сообщения от разрешенного пользователя"""
    with patch.dict('os.environ', {'ALLOWED_CHAT_IDS': '123456789,987654321'}):
        message = AsyncMock(spec=Message)
        message.from_user = MagicMock(spec=User)
        message.from_user.id = 123456789  # ID пользователя из списка разрешенных
        message.chat = MagicMock(spec=Chat)
        message.chat.id = 123456789
        message.answer = AsyncMock(return_value=None)
        yield message

@pytest.fixture
def mock_unauthorized_user():
    """Создает мок сообщения от неразрешенного пользователя"""
    with patch.dict('os.environ', {'ALLOWED_CHAT_IDS': '111111,222222'}):
        message = AsyncMock(spec=Message)
        message.from_user = MagicMock(spec=User)
        message.from_user.id = 999999  # ID пользователя не из списка разрешенных
        message.chat = MagicMock(spec=Chat)
        message.chat.id = 999999
        message.answer = AsyncMock(return_value=None)
        yield message

# Патч для функции is_authorized в тестируемых методах
@pytest.fixture
def patch_is_authorized():
    with patch('bot.is_authorized', return_value=True) as mock:
        yield mock

# Тесты для авторизации
@pytest.mark.asyncio
async def test_is_authorized_allowed():
    """Тест авторизации для разрешенного пользователя"""
    # Для корректной работы нужно патчить ALLOWED_CHAT_IDS в модуле bot
    with patch.object(bot, 'ALLOWED_CHAT_IDS', ['123456789', '987654321']):
        message = AsyncMock(spec=Message)
        message.from_user = MagicMock(spec=User)
        message.from_user.id = 123456789
        message.chat = MagicMock(spec=Chat)
        message.chat.id = 123456789
        message.answer = AsyncMock()
        
        # Если ID пользователя число
        message.from_user.id = 123456789
        result = await is_authorized(message)
        assert result is True, "Разрешенный пользователь (числовой ID) должен быть авторизован"
        
        # Если ID пользователя в строке
        message.from_user.id = '123456789'
        result = await is_authorized(message)
        assert result is True, "Разрешенный пользователь (строковый ID) должен быть авторизован"
        
        message.answer.assert_not_called()

@pytest.mark.asyncio
async def test_is_authorized_not_allowed():
    """Тест авторизации для неразрешенного пользователя"""
    # Для корректной работы нужно патчить ALLOWED_CHAT_IDS в модуле bot
    with patch.object(bot, 'ALLOWED_CHAT_IDS', ['111111', '222222']):
        message = AsyncMock(spec=Message)
        message.from_user = MagicMock(spec=User)
        message.from_user.id = 999999
        message.chat = MagicMock(spec=Chat)
        message.chat.id = 999999
        message.answer = AsyncMock()
        
        result = await is_authorized(message)
        assert result is False, "Неразрешенный пользователь не должен быть авторизован"
        message.answer.assert_called_once()

# Тесты для команд бота
@pytest.mark.asyncio
async def test_send_welcome(patch_is_authorized):
    """Тест команды /start и /help"""
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    
    await send_welcome(message)
    
    message.answer.assert_called_once()
    # Проверяем, что сообщение содержит ключевые слова
    call_args = message.answer.call_args[0][0]
    assert "Привет" in call_args, "Приветственное сообщение должно содержать слово 'Привет'"
    assert "/status" in call_args, "Приветственное сообщение должно содержать описание команды /status"
    assert "/monitors" in call_args, "Приветственное сообщение должно содержать описание команды /monitors"
    assert "/incidents" in call_args, "Приветственное сообщение должно содержать описание команды /incidents"

# Патчим UptimeKumaClient для тестирования команд, работающих с API
@pytest.mark.asyncio
@patch('bot.UptimeKumaClient')
async def test_get_status(mock_client_class, patch_is_authorized):
    """Тест команды /status"""
    # Создаем мок сообщения
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    
    # Настраиваем мок для клиента
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    
    # Имитируем данные для get_status_summary
    mock_client.get_status_summary.return_value = {
        "total": 5,
        "up": 3,
        "down": 1,
        "maintenance": 1,
        "uptime": 80.0
    }
    
    # Имитируем данные для get_monitors (проблемные сервисы)
    mock_client.get_monitors.return_value = [
        {"id": "1", "name": "Сервис 1", "status": 1, "active": True, "maintenance": False},
        {"id": "2", "name": "Сервис 2", "status": 0, "active": True, "maintenance": False},
        {"id": "3", "name": "Сервис 3", "status": 1, "active": True, "maintenance": False},
        {"id": "4", "name": "Сервис 4", "status": 1, "active": True, "maintenance": False},
        {"id": "5", "name": "Сервис 5", "status": 0, "active": True, "maintenance": True}
    ]
    
    # Вызываем тестируемую функцию
    await get_status(message)
    
    # Проверяем, что было вызвано 2 ответа: "Получаю статус..." и сам статус
    assert message.answer.call_count == 2, "Должно быть отправлено 2 сообщения"
    
    # Проверяем содержимое последнего сообщения (статус)
    call_args = message.answer.call_args[0][0]
    assert "Статус сервисов" in call_args, "Сообщение должно содержать заголовок о статусе"
    assert "Всего: 5" in call_args, "Сообщение должно содержать общее количество сервисов"
    assert "Работают: 3" in call_args, "Сообщение должно содержать количество работающих сервисов"
    assert "Не работают: 1" in call_args, "Сообщение должно содержать количество неработающих сервисов"
    assert "Uptime: 80.0%" in call_args, "Сообщение должно содержать процент uptime"
    assert "Сервисы с проблемами" in call_args, "Сообщение должно содержать список проблемных сервисов"
    assert "Сервис 2" in call_args, "В сообщении должен быть указан проблемный сервис"

@pytest.mark.asyncio
@patch('bot.UptimeKumaClient')
async def test_list_monitors(mock_client_class, patch_is_authorized):
    """Тест команды /monitors"""
    # Создаем мок сообщения
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    
    # Настраиваем мок для клиента
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    
    # Имитируем данные для get_monitors
    mock_client.get_monitors.return_value = [
        {"id": "1", "name": "Сервис 1", "status": 1, "active": True, "maintenance": False, "url": "http://example.com"},
        {"id": "2", "name": "Сервис 2", "status": 0, "active": True, "maintenance": False, "url": "http://example2.com"}
    ]
    
    # Вызываем тестируемую функцию
    await list_monitors(message)
    
    # Проверяем, что было вызвано 2 ответа: "Получаю список..." и сам список
    assert message.answer.call_count == 2, "Должно быть отправлено 2 сообщения"
    
    # Проверяем содержимое последнего сообщения (список мониторов)
    call_args = message.answer.call_args[0][0]
    assert "Список мониторов" in call_args, "Сообщение должно содержать заголовок списка мониторов"
    assert "Сервис 1" in call_args, "Сообщение должно содержать имя первого сервиса"
    assert "Сервис 2" in call_args, "Сообщение должно содержать имя второго сервиса"
    assert "http://example.com" in call_args, "Сообщение должно содержать URL первого сервиса"
    assert "http://example2.com" in call_args, "Сообщение должно содержать URL второго сервиса"

@pytest.mark.asyncio
@patch('bot.UptimeKumaClient')
async def test_list_incidents(mock_client_class, patch_is_authorized):
    """Тест команды /incidents"""
    # Создаем мок сообщения
    message = AsyncMock(spec=Message)
    message.answer = AsyncMock()
    
    # Настраиваем мок для клиента
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    
    # Имитируем данные для get_incidents
    mock_client.get_incidents.return_value = [
        {
            "id": "1", 
            "title": "Проблема с сервисом 1", 
            "monitor_name": "Сервис 1", 
            "status": "down", 
            "started_at": "2023-01-01 10:00", 
            "resolved_at": None
        }
    ]
    
    # Вызываем тестируемую функцию
    await list_incidents(message)
    
    # Проверяем, что было вызвано 2 ответа: "Получаю список..." и сам список
    assert message.answer.call_count == 2, "Должно быть отправлено 2 сообщения"
    
    # Проверяем содержимое последнего сообщения (список инцидентов)
    call_args = message.answer.call_args[0][0]
    assert "Список инцидентов" in call_args, "Сообщение должно содержать заголовок списка инцидентов"
    assert "Проблема с сервисом 1" in call_args, "Сообщение должно содержать название инцидента"
    assert "Сервис 1" in call_args, "Сообщение должно содержать имя сервиса"
    assert "down" in call_args, "Сообщение должно содержать статус инцидента"
    assert "2023-01-01 10:00" in call_args, "Сообщение должно содержать время начала инцидента" 