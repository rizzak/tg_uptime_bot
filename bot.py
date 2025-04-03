from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
import asyncio
from dotenv import load_dotenv
import os
import logging
from uptime_kuma_client import UptimeKumaClient

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()  # Загрузка переменных окружения из .env

# Получение настроек из переменных окружения
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_CHAT_IDS = os.getenv('ALLOWED_CHAT_IDS', '').split(',')

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Проверка доступа
async def is_authorized(message: Message) -> bool:
    """Проверяет, авторизован ли пользователь для использования бота"""
    user_id = str(message.from_user.id)
    if user_id in ALLOWED_CHAT_IDS:
        return True
    await message.answer("У вас нет доступа к этому боту.")
    return False

@dp.message(Command(commands=['start', 'help']))
async def send_welcome(message: Message):
    """Обработчик команд /start и /help"""
    if not await is_authorized(message):
        return
    
    await message.answer(
        "👋 Привет! Я бот для мониторинга Uptime Kuma.\n\n"
        "Доступные команды:\n"
        "/status - Получить общий статус всех сервисов\n"
        "/monitors - Показать список всех мониторов\n"
        "/incidents - Показать список инцидентов"
    )

@dp.message(Command(commands=['status']))
async def get_status(message: Message):
    """Получение общего статуса всех сервисов"""
    if not await is_authorized(message):
        return
    
    await message.answer("🔍 Получаю статус сервисов...")
    
    try:
        async with UptimeKumaClient() as client:
            # Получаем сводку по статусу
            summary = await client.get_status_summary()
            
            response = f"📊 Статус сервисов:\n\n"
            response += f"Всего: {summary['total']}\n"
            response += f"✅ Работают: {summary['up']}\n"
            response += f"❌ Не работают: {summary['down']}\n"
            response += f"🔧 На обслуживании: {summary['maintenance']}\n"
            response += f"📈 Uptime: {summary['uptime']}%\n"
            
            # Если есть неработающие сервисы, покажем их
            if summary['down'] > 0:
                response += "\n⚠️ Сервисы с проблемами:\n"
                
                # Получаем список всех мониторов
                monitors = await client.get_monitors()
                for monitor in monitors:
                    if monitor['status'] == 0 and monitor['active'] and not monitor['maintenance']:
                        response += f"- {monitor['name']}\n"
            
            await message.answer(response)
    except Exception as e:
        logger.error(f"Ошибка при получении статуса: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@dp.message(Command(commands=['monitors']))
async def list_monitors(message: Message):
    """Получение списка всех мониторов"""
    if not await is_authorized(message):
        return
    
    await message.answer("🔍 Получаю список мониторов...")
    
    try:
        async with UptimeKumaClient() as client:
            monitors = await client.get_monitors()
            
            if not monitors:
                await message.answer("❗ Мониторы не найдены.")
                return
            
            response = "📋 Список мониторов:\n\n"
            
            for monitor in monitors:
                status_emoji = "✅" if monitor['status'] == 1 else "❌"
                if monitor.get('maintenance', False):
                    status_emoji = "🔧"
                
                response += f"{status_emoji} {monitor['name']}"
                if monitor.get('url'):
                    response += f" ({monitor['url']})"
                response += "\n"
            
            await message.answer(response)
    except Exception as e:
        logger.error(f"Ошибка при получении списка мониторов: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

@dp.message(Command(commands=['incidents']))
async def list_incidents(message: Message):
    """Получение списка инцидентов"""
    if not await is_authorized(message):
        return
    
    await message.answer("🔍 Получаю список инцидентов...")
    
    try:
        async with UptimeKumaClient() as client:
            incidents = await client.get_incidents()
            
            if not incidents:
                await message.answer("✅ Активных инцидентов нет.")
                return
            
            response = "🚨 Список инцидентов:\n\n"
            
            for incident in incidents:
                response += f"⚠️ {incident['title']}\n"
                response += f"Монитор: {incident['monitor_name']}\n"
                response += f"Статус: {incident['status']}\n"
                response += f"Начало: {incident['started_at']}\n"
                if incident.get('resolved_at'):
                    response += f"Разрешено: {incident['resolved_at']}\n"
                response += "\n"
            
            await message.answer(response)
    except Exception as e:
        logger.error(f"Ошибка при получении списка инцидентов: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 