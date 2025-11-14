"""
Все репозитории для базы данных
Содержит: Students, Teachers, Courses, Groups, Admins, Lessons, Feedback, Reminders
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ReminderRepository:
    """Репозиторий для работы с напоминаниями"""

    def __init__(self, db):
        self.db = db

    def create(self, user_id: int, text: str, due_date: str) -> Optional[int]:
        """Создать напоминание"""
        try:
            query = """
                    INSERT INTO reminders (user_id, text, due_date)
                    VALUES (?, ?, ?)
                    """
            reminder_id = self.db.execute_insert(query, (user_id, text, due_date))
            logger.info(f"Created reminder {reminder_id} for user {user_id}")
            return reminder_id
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            return None

    def get_pending(self) -> List[Dict]:
        """Получить все неотправленные напоминания с наступившим сроком"""
        query = """
                SELECT r.*, u.telegram_id, u.full_name
                FROM reminders r
                         JOIN users u ON r.user_id = u.id
                WHERE r.sent = 0 
                  AND r.due_date <= datetime('now')
                ORDER BY r.due_date 
                """
        return self.db.execute_query(query)

    def mark_sent(self, reminder_id: int) -> bool:
        """Отметить напоминание как отправленное"""
        try:
            query = "UPDATE reminders SET sent = 1 WHERE id = ?"
            affected = self.db.execute_update(query, (reminder_id,))
            return affected > 0
        except Exception as e:
            logger.error(f"Error marking reminder as sent: {e}")
            return False
















