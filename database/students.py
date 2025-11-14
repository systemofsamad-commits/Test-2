# students.py - ПРАВИЛЬНАЯ ВЕРСИЯ
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class StudentRepository:
    """Репозиторий для работы со студентами"""

    def __init__(self, db):
        self.db = db

    def create(self, user_id: int, student_code: Optional[str] = None) -> Optional[int]:
        """Создать студента"""
        try:
            query = """
                    INSERT INTO students (user_id, student_code)
                    VALUES (?, ?)
                    """
            student_id = self.db.execute_insert(query, (user_id, student_code))
            logger.info(f"Created student {student_id} for user {user_id}")
            return student_id
        except Exception as e:
            logger.error(f"Error creating student: {e}")
            return None

    def get_by_user_id(self, user_id: int) -> Optional[Dict]:
        """Получить студента по ID пользователя"""
        query = """
                SELECT s.*, u.full_name, u.phone, u.telegram_id
                FROM students s
                JOIN users u ON s.user_id = u.id
                WHERE s.user_id = ?
                """
        rows = self.db.execute_query(query, (user_id,))
        return rows[0] if rows else None

    def get_all_active(self) -> List[Dict]:
        """Получить всех активных студентов"""
        query = """
                SELECT s.*, u.full_name, u.phone, u.telegram_id
                FROM students s
                JOIN users u ON s.user_id = u.id
                WHERE s.is_active = 1
                ORDER BY u.full_name
                """
        return self.db.execute_query(query)