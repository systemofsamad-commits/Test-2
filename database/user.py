import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class UserRepository:
    """Репозиторий для работы с пользователями"""

    def __init__(self, db):
        self.db = db

    def create_or_update(self, telegram_id: int, username: Optional[str] = None,
                        full_name: Optional[str] = None, phone: Optional[str] = None) -> Optional[int]:
        """Создать или обновить пользователя"""
        try:
            query = """
                    INSERT INTO users (telegram_id, username, full_name, phone)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(telegram_id) DO UPDATE SET
                        username = excluded.username,
                        full_name = excluded.full_name,
                        phone = COALESCE(excluded.phone, phone),
                        updated_at = CURRENT_TIMESTAMP
                    """
            user_id = self.db.execute_insert(query, (telegram_id, username, full_name, phone))
            return user_id
        except Exception as e:
            logger.error(f"Error creating/updating user: {e}")
            return None

    def get_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Получить пользователя по Telegram ID"""
        query = "SELECT * FROM users WHERE telegram_id = ?"
        rows = self.db.execute_query(query, (telegram_id,))
        return rows[0] if rows else None

    def get_by_id(self, user_id: int) -> Optional[Dict]:
        """Получить пользователя по ID"""
        query = "SELECT * FROM users WHERE id = ?"
        rows = self.db.execute_query(query, (user_id,))
        return rows[0] if rows else None