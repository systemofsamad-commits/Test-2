"""
Все репозитории для базы данных
Содержит: Students, Teachers, Courses, Groups, Admins, Lessons, Feedback, Reminders
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class TeacherRepository:
    """Репозиторий для работы с преподавателями"""

    def __init__(self, db):
        self.db = db

    def create(self, name: str, phone: str, email: Optional[str] = None,
               specialization: Optional[str] = None, experience: Optional[str] = None) -> Optional[int]:
        """Создать преподавателя"""
        try:
            query = """
                    INSERT INTO teachers (name, phone, email, specialization, experience)
                    VALUES (?, ?, ?, ?, ?)
                    """
            teacher_id = self.db.execute_insert(query, (name, phone, email, specialization, experience))
            logger.info(f"Created teacher {teacher_id}: {name}")
            return teacher_id
        except Exception as e:
            logger.error(f"Error creating teacher: {e}")
            return None

    def get_all_active(self) -> List[Dict]:
        """Получить всех активных преподавателей"""
        query = "SELECT * FROM teachers WHERE is_active = 1 ORDER BY name"
        return self.db.execute_query(query)

    def get_by_id(self, teacher_id: int) -> Optional[Dict]:
        """Получить преподавателя по ID"""
        query = "SELECT * FROM teachers WHERE id = ?"
        rows = self.db.execute_query(query, (teacher_id,))
        return rows[0] if rows else None

    def update(self, teacher_id: int, **kwargs) -> bool:
        """Обновить данные преподавателя"""
        try:
            allowed_fields = ['name', 'phone', 'email', 'specialization', 'experience', 'bio']
            updates = []
            params = []

            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates.append(f"{field} = ?")
                    params.append(value)

            if not updates:
                return False

            params.append(teacher_id)
            query = f"UPDATE teachers SET {', '.join(updates)} WHERE id = ?"
            affected = self.db.execute_update(query, tuple(params))
            return affected > 0
        except Exception as e:
            logger.error(f"Error updating teacher: {e}")
            return False

    def deactivate(self, teacher_id: int) -> bool:
        """Деактивировать преподавателя"""
        try:
            query = "UPDATE teachers SET is_active = 0 WHERE id = ?"
            affected = self.db.execute_update(query, (teacher_id,))
            return affected > 0
        except Exception as e:
            logger.error(f"Error deactivating teacher: {e}")
            return False