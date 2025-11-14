"""
Все репозитории для базы данных
Содержит: Students, Teachers, Courses, Groups, Admins, Lessons, Feedback, Reminders
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class AdminRepository:
    """Репозиторий для работы с администраторами"""

    def __init__(self, db):
        self.db = db

    def create(self, user_id: int, username: Optional[str] = None,
               full_name: Optional[str] = None) -> Optional[int]:
        """Создать администратора"""
        try:
            query = """
                    INSERT INTO admins (user_id, username, full_name)
                    VALUES (?, ?, ?)
                    """
            admin_id = self.db.execute_insert(query, (user_id, username, full_name))
            logger.info(f"Created admin {admin_id} for user {user_id}")
            return admin_id
        except Exception as e:
            logger.error(f"Error creating admin: {e}")
            return None

    def get_all(self) -> List[Dict]:
        """Получить всех администраторов"""
        query = "SELECT * FROM admins WHERE is_active = 1 ORDER BY created_at DESC"
        return self.db.execute_query(query)

    def is_admin(self, user_id: int) -> bool:
        """Проверить является ли пользователь администратором"""
        query = "SELECT id FROM admins WHERE user_id = ? AND is_active = 1"
        rows = self.db.execute_query(query, (user_id,))
        return len(rows) > 0

    def deactivate(self, admin_id: int) -> bool:
        """Деактивировать администратора"""
        try:
            query = "UPDATE admins SET is_active = 0 WHERE id = ?"
            affected = self.db.execute_update(query, (admin_id,))
            return affected > 0
        except Exception as e:
            logger.error(f"Error deactivating admin: {e}")
            return False