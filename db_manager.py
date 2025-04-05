import sqlite3
import logging
import os
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
import datetime

# Настройка логирования
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """Роли пользователей в БД"""
    ADMIN = "admin"
    USER = "user"
    BLOCKED = "blocked"

class PaymentStatus(Enum):
    """Статусы платежей"""
    PENDING = "pending"  # Ожидает оплаты
    PAID = "paid"        # Оплачено
    EXPIRED = "expired"  # Просрочено
    CANCELLED = "cancelled" # Отменено

class DBManager:
    """Класс для управления базой данных SQLite"""
    
    def __init__(self, db_path: str = "data/bot_database.db"):
        """Инициализация менеджера базы данных
        
        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = db_path
        # Создаем директорию, если её нет
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._create_tables()
        
    def _get_connection(self) -> sqlite3.Connection:
        """Устанавливает соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Возвращать строки как словари
        return conn
    
    def _create_tables(self):
        """Создает необходимые таблицы в базе данных, если они не существуют"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Таблица пользователей
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,      -- Telegram User ID
                role TEXT NOT NULL,             -- Роль (admin, user, blocked)
                name TEXT,                      -- Имя пользователя (из Telegram)
                username TEXT,                  -- Username (из Telegram)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Дата создания
                subscription_expires_at TIMESTAMP NULL -- Дата окончания подписки
            )
            """)
            
            # Таблица мониторингов Uptime Kuma
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitors (
                monitor_id INTEGER PRIMARY KEY,   -- ID мониторинга в Uptime Kuma
                name TEXT NOT NULL,             -- Имя мониторинга
                url TEXT,                       -- URL мониторинга
                type TEXT                       -- Тип мониторинга
            )
            """)
            
            # Связующая таблица: Пользователи <-> Мониторинги
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_monitors (
                user_id INTEGER NOT NULL,
                monitor_id INTEGER NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Дата добавления связи
                PRIMARY KEY (user_id, monitor_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                FOREIGN KEY (monitor_id) REFERENCES monitors (monitor_id) ON DELETE CASCADE
            )
            """)
            
            # Таблица платежей/подписок
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,                   -- Сумма платежа
                status TEXT NOT NULL,                   -- Статус (pending, paid, expired, cancelled)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- Дата создания платежа
                paid_at TIMESTAMP NULL,                 -- Дата оплаты
                expires_at TIMESTAMP NOT NULL,            -- Дата окончания действия подписки
                payment_provider TEXT,                -- Провайдер платежа (например, Stripe, ЮKassa)
                provider_payment_id TEXT,             -- ID платежа у провайдера
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
            """)
            
            conn.commit()
            logger.info("Таблицы в базе данных успешно созданы или уже существуют.")
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка при создании таблиц: {e}", exc_info=True)
            conn.rollback()
        finally:
            conn.close()
            
    # --- Методы для управления пользователями ---
    
    def add_or_update_user(self, user_id: int, role: UserRole, name: Optional[str] = None, username: Optional[str] = None) -> bool:
        """Добавляет нового пользователя или обновляет роль/имя существующего"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO users (user_id, role, name, username) 
            VALUES (?, ?, ?, ?) 
            ON CONFLICT(user_id) DO UPDATE SET 
            role=excluded.role, name=excluded.name, username=excluded.username
            """, (user_id, role.value, name, username))
            conn.commit()
            logger.info(f"Пользователь {user_id} добавлен/обновлен с ролью {role.value}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка при добавлении/обновлении пользователя {user_id}: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()
            
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о пользователе по ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user_row = cursor.fetchone()
            return dict(user_row) if user_row else None
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении пользователя {user_id}: {e}", exc_info=True)
            return None
        finally:
            conn.close()
            
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получает список всех пользователей"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users")
            users = [dict(row) for row in cursor.fetchall()]
            return users
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении списка всех пользователей: {e}", exc_info=True)
            return []
        finally:
            conn.close()
            
    def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя по ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()
            # Проверяем, была ли действительно удалена строка
            if cursor.rowcount > 0:
                logger.info(f"Пользователь {user_id} удален")
                return True
            else:
                logger.warning(f"Попытка удаления несуществующего пользователя: {user_id}")
                return False
        except sqlite3.Error as e:
            logger.error(f"Ошибка при удалении пользователя {user_id}: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()
            
    def get_users_by_role(self, role: UserRole) -> List[Dict[str, Any]]:
        """Получает список пользователей с указанной ролью"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE role = ?", (role.value,))
            users = [dict(row) for row in cursor.fetchall()]
            return users
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении пользователей с ролью {role.value}: {e}", exc_info=True)
            return []
        finally:
            conn.close()
            
    # --- Методы для управления мониторингами --- 
    
    def add_or_update_monitor(self, monitor_id: int, name: str, url: Optional[str] = None, type: Optional[str] = None) -> bool:
        """Добавляет или обновляет информацию о мониторинге"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO monitors (monitor_id, name, url, type) 
            VALUES (?, ?, ?, ?) 
            ON CONFLICT(monitor_id) DO UPDATE SET 
            name=excluded.name, url=excluded.url, type=excluded.type
            """, (monitor_id, name, url, type))
            conn.commit()
            logger.info(f"Мониторинг {monitor_id} добавлен/обновлен: {name}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка при добавлении/обновлении мониторинга {monitor_id}: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()
            
    def get_monitor(self, monitor_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о мониторинге по ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM monitors WHERE monitor_id = ?", (monitor_id,))
            monitor_row = cursor.fetchone()
            return dict(monitor_row) if monitor_row else None
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении мониторинга {monitor_id}: {e}", exc_info=True)
            return None
        finally:
            conn.close()
            
    # --- Методы для управления связями Пользователь <-> Мониторинг ---
    
    def assign_monitor_to_user(self, user_id: int, monitor_id: int) -> bool:
        """Назначает мониторинг пользователю"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT OR IGNORE INTO user_monitors (user_id, monitor_id) VALUES (?, ?)", (user_id, monitor_id))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"Мониторинг {monitor_id} назначен пользователю {user_id}")
                return True
            else:
                logger.warning(f"Связь пользователя {user_id} и мониторинга {monitor_id} уже существует")
                return False
        except sqlite3.Error as e:
            logger.error(f"Ошибка при назначении мониторинга {monitor_id} пользователю {user_id}: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()
            
    def unassign_monitor_from_user(self, user_id: int, monitor_id: int) -> bool:
        """Отвязывает мониторинг от пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM user_monitors WHERE user_id = ? AND monitor_id = ?", (user_id, monitor_id))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"Мониторинг {monitor_id} отвязан от пользователя {user_id}")
                return True
            else:
                logger.warning(f"Связь пользователя {user_id} и мониторинга {monitor_id} не найдена")
                return False
        except sqlite3.Error as e:
            logger.error(f"Ошибка при отвязке мониторинга {monitor_id} от пользователя {user_id}: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()
            
    def get_user_monitors(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает список мониторингов, назначенных пользователю"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
            SELECT m.* 
            FROM monitors m
            JOIN user_monitors um ON m.monitor_id = um.monitor_id
            WHERE um.user_id = ?
            """, (user_id,))
            monitors = [dict(row) for row in cursor.fetchall()]
            return monitors
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении мониторингов пользователя {user_id}: {e}", exc_info=True)
            return []
        finally:
            conn.close()
            
    # --- Методы для управления платежами/подписками ---
    
    def create_payment(self, user_id: int, amount: float, status: PaymentStatus, expires_at: datetime.datetime, 
                       payment_provider: Optional[str] = None, provider_payment_id: Optional[str] = None) -> Optional[int]:
        """Создает запись о новом платеже/подписке"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
            INSERT INTO payments (user_id, amount, status, expires_at, payment_provider, provider_payment_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, amount, status.value, expires_at, payment_provider, provider_payment_id))
            conn.commit()
            payment_id = cursor.lastrowid
            logger.info(f"Создан платеж ID {payment_id} для пользователя {user_id}")
            return payment_id
        except sqlite3.Error as e:
            logger.error(f"Ошибка при создании платежа для пользователя {user_id}: {e}", exc_info=True)
            conn.rollback()
            return None
        finally:
            conn.close()
            
    def update_payment_status(self, payment_id: int, status: PaymentStatus, paid_at: Optional[datetime.datetime] = None) -> bool:
        """Обновляет статус платежа"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if status == PaymentStatus.PAID and paid_at is None:
                paid_at = datetime.datetime.now()
                
            cursor.execute("UPDATE payments SET status = ?, paid_at = ? WHERE payment_id = ?", 
                           (status.value, paid_at, payment_id))
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(f"Статус платежа ID {payment_id} обновлен на {status.value}")
                # Обновляем дату окончания подписки пользователя
                if status == PaymentStatus.PAID:
                    payment_info = self.get_payment(payment_id)
                    if payment_info:
                        self.update_user_subscription_expiry(payment_info['user_id'], payment_info['expires_at'])
                return True
            else:
                logger.warning(f"Платеж с ID {payment_id} не найден для обновления статуса")
                return False
        except sqlite3.Error as e:
            logger.error(f"Ошибка при обновлении статуса платежа ID {payment_id}: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()
            
    def get_payment(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """Получает информацию о платеже по ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
            payment_row = cursor.fetchone()
            return dict(payment_row) if payment_row else None
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении платежа ID {payment_id}: {e}", exc_info=True)
            return None
        finally:
            conn.close()

    def get_user_payments(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает все платежи пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            payments = [dict(row) for row in cursor.fetchall()]
            return payments
        except sqlite3.Error as e:
            logger.error(f"Ошибка при получении платежей пользователя {user_id}: {e}", exc_info=True)
            return []
        finally:
            conn.close()
            
    def update_user_subscription_expiry(self, user_id: int, expires_at: datetime.datetime) -> bool:
        """Обновляет дату окончания подписки пользователя"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET subscription_expires_at = ? WHERE user_id = ?", (expires_at, user_id))
            conn.commit()
            logger.info(f"Дата окончания подписки для пользователя {user_id} обновлена на {expires_at}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Ошибка при обновлении даты подписки пользователя {user_id}: {e}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()
            
    def check_subscription_status(self, user_id: int) -> bool:
        """Проверяет, активна ли подписка пользователя"""
        user_info = self.get_user(user_id)
        if not user_info or not user_info['subscription_expires_at']:
            return False
            
        try:
            expires_at = datetime.datetime.fromisoformat(user_info['subscription_expires_at'])
            return expires_at > datetime.datetime.now()
        except ValueError:
            logger.error(f"Неверный формат даты подписки для пользователя {user_id}: {user_info['subscription_expires_at']}")
            return False

# Пример использования:
if __name__ == '__main__':
    # Настройка базового логирования для примера
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    db = DBManager()
    
    # Добавляем пользователя
    db.add_or_update_user(12345, UserRole.ADMIN, "Admin User", "admin_tg")
    db.add_or_update_user(67890, UserRole.USER, "Regular User", "user_tg")
    
    # Получаем пользователя
    admin = db.get_user(12345)
    print(f"Admin: {admin}")
    
    # Добавляем мониторинг
    db.add_or_update_monitor(1, "Google", "https://google.com", "HTTP")
    db.add_or_update_monitor(2, "Yandex", "https://yandex.ru", "HTTP")
    
    # Назначаем мониторинги пользователю
    db.assign_monitor_to_user(67890, 1)
    db.assign_monitor_to_user(67890, 2)
    
    # Получаем мониторинги пользователя
    user_monitors = db.get_user_monitors(67890)
    print(f"User 67890 monitors: {user_monitors}")
    
    # Создаем платеж
    expires = datetime.datetime.now() + datetime.timedelta(days=30)
    payment_id = db.create_payment(67890, 100.0, PaymentStatus.PENDING, expires)
    print(f"Created payment ID: {payment_id}")
    
    # Обновляем статус платежа
    if payment_id:
        db.update_payment_status(payment_id, PaymentStatus.PAID)
        
    # Проверяем статус подписки
    is_active = db.check_subscription_status(67890)
    print(f"User 67890 subscription active: {is_active}")
    
    # Получаем все платежи пользователя
    user_payments = db.get_user_payments(67890)
    print(f"User 67890 payments: {user_payments}") 