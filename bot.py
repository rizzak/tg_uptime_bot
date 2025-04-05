from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
import asyncio
from dotenv import load_dotenv
import os
import logging
from uptime_kuma_client import UptimeKumaClient
from db_manager import DBManager, UserRole
from typing import Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv(override=True)  # Загрузка переменных окружения из .env с перезаписью

# Получение настроек из переменных окружения
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
db_manager = DBManager()

# Проверка доступа
async def is_authorized(message: Message) -> bool:
    """Проверяет, авторизован ли пользователь для использования бота (не заблокирован ли он)"""
    user_id = message.from_user.id
    user_info = db_manager.get_user(user_id)

    if user_info and user_info['role'] != UserRole.BLOCKED:
        # Пользователь найден в БД и не заблокирован
        return True
    
    # Пользователь не найден или заблокирован
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
        async with asyncio.timeout(30):
            logger.info("Создание экземпляра UptimeKumaClient...")
            async with UptimeKumaClient() as client:
                logger.info("Экземпляр UptimeKumaClient создан. Вызов get_status_summary...")
                summary = await client.get_status_summary()
                logger.info("Получен ответ от get_status_summary.")
                
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
    except asyncio.TimeoutError:
        logger.error("Таймаут при обращении к Uptime Kuma")
        await message.answer("🕒 Не удалось получить ответ от Uptime Kuma вовремя. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Ошибка при работе с Uptime Kuma: {e}")
        await message.answer(f"❌ Произошла ошибка при связи с Uptime Kuma: {str(e)}")

@dp.message(Command(commands=['monitors']))
async def list_monitors(message: Message):
    """Получение списка всех мониторов"""
    if not await is_authorized(message):
        return
    
    await message.answer("🔍 Получаю список мониторов...")
    
    try:
        async with asyncio.timeout(30):
            logger.info("Создание экземпляра UptimeKumaClient...")
            async with UptimeKumaClient() as client:
                logger.info("Экземпляр UptimeKumaClient создан. Вызов get_monitors...")
                monitors = await client.get_monitors()
                logger.info("Получен ответ от get_monitors.")
                
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
    except asyncio.TimeoutError:
        logger.error("Таймаут при получении списка мониторов от Uptime Kuma")
        await message.answer("🕒 Не удалось получить список мониторов от Uptime Kuma вовремя. Попробуйте позже.")
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
        async with asyncio.timeout(30):
            logger.info("Создание экземпляра UptimeKumaClient...")
            async with UptimeKumaClient() as client:
                logger.info("Экземпляр UptimeKumaClient создан. Вызов get_incidents...")
                incidents = await client.get_incidents()
                logger.info("Получен ответ от get_incidents.")
                
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
    except asyncio.TimeoutError:
        logger.error("Таймаут при получении списка инцидентов от Uptime Kuma")
        await message.answer("🕒 Не удалось получить список инцидентов от Uptime Kuma вовремя. Попробуйте позже.")
    except Exception as e:
        logger.error(f"Ошибка при получении списка инцидентов: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

# --- Инициализация приложения ---
async def initialize_app():
    """Инициализирует приложение, синхронизирует админа из .env с БД."""
    logger.info("Инициализация приложения и синхронизация администратора...")
    
    new_admin_id_str = os.getenv('ADMIN_CHAT_ID')
    new_admin_id: Optional[int] = None

    if new_admin_id_str:
        try:
            new_admin_id = int(new_admin_id_str)
        except ValueError:
            logger.error(f"Неверный формат ADMIN_CHAT_ID: {new_admin_id_str}. Должно быть целое число. Инициализация администратора пропущена.")
            new_admin_id = None # Сбрасываем, чтобы не обрабатывать дальше
    else:
        logger.warning("ADMIN_CHAT_ID не указан в .env. Пропускаем синхронизацию администратора. Убедитесь, что администратор назначен вручную, если это необходимо.")

    # Получаем текущих админов из БД
    current_admins = db_manager.get_users_by_role(UserRole.ADMIN)
    current_admin_ids = {admin['user_id'] for admin in current_admins}

    # 1. Демоут (понижение роли) старых админов, если ID изменился
    if new_admin_id is not None: # Если новый админ задан
        for admin in current_admins:
            admin_id_db = admin['user_id']
            if admin_id_db != new_admin_id:
                logger.info(f"Обнаружено изменение ADMIN_CHAT_ID. Понижение роли предыдущего администратора {admin_id_db} до USER.")
                # Понижаем роль до USER, сохраняя имя/username
                db_manager.add_or_update_user(admin_id_db, UserRole.USER, name=admin.get('name'), username=admin.get('username'))
                current_admin_ids.remove(admin_id_db) # Убираем из текущих, чтобы не обновлять его как админа ниже
    # Если new_admin_id не задан, не трогаем существующих админов

    # 2. Промоут (повышение роли) нового админа, если он задан
    if new_admin_id is not None and new_admin_id not in current_admin_ids:
        logger.info(f"Установка пользователя {new_admin_id} как администратора согласно ADMIN_CHAT_ID.")
        try:
            # Пытаемся получить информацию о пользователе из Telegram API
            try:
                admin_user_info = await bot.get_chat(new_admin_id)
                admin_name = admin_user_info.full_name
                admin_username = admin_user_info.username
            except Exception as e:
                logger.warning(f"Не удалось получить информацию о пользователе {new_admin_id} из Telegram API: {e}. Используем стандартные значения.")
                admin_name = f"Admin_{new_admin_id}"
                admin_username = None
            
            # Добавляем или обновляем админа в БД
            if db_manager.add_or_update_user(new_admin_id, UserRole.ADMIN, name=admin_name, username=admin_username):
                logger.info(f"Администратор {admin_name} ({new_admin_id}) успешно добавлен/обновлен в БД с ролью ADMIN.")
            else:
                logger.error(f"Не удалось добавить/обновить администратора {new_admin_id} в БД.")
                
        except Exception as e:
            logger.error(f"Критическая ошибка при назначении нового администратора ({new_admin_id}): {e}", exc_info=True)
    elif new_admin_id is not None:
         logger.info(f"Пользователь {new_admin_id} уже является администратором.")

    logger.info("Синхронизация администратора завершена.")
# --- Конец инициализации ---

async def main():
    await initialize_app()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 