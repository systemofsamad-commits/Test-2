"""
Все репозитории для базы данных
Содержит: Students, Teachers, Courses, Groups, Admins, Lessons, Feedback, Reminders
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class CourseRepository:
    """Репозиторий для работы с курсами"""

    def __init__(self, db):
        self.db = db

    def get_all_active(self) -> List[Dict]:
        """Получить все активные курсы"""
        query = "SELECT * FROM courses WHERE is_active = 1 ORDER BY name"
        return self.db.execute_query(query)

    def get_by_id(self, course_id: int) -> Optional[Dict]:
        """Получить курс по ID"""
        query = "SELECT * FROM courses WHERE id = ?"
        rows = self.db.execute_query(query, (course_id,))
        return rows[0] if rows else None

    def get_by_name(self, name: str) -> Optional[Dict]:
        """Получить курс по названию"""
        query = "SELECT * FROM courses WHERE name = ?"
        rows = self.db.execute_query(query, (name,))
        return rows[0] if rows else None

    def create(self, name: str, description: Optional[str] = None,
               duration_months: Optional[int] = None, price_group: Optional[int] = None,
               price_individual: Optional[int] = None) -> Optional[int]:
        """Создать курс"""
        try:
            query = """
                    INSERT INTO courses (name, description, duration_months, price_group, price_individual)
                    VALUES (?, ?, ?, ?, ?)
                    """
            course_id = self.db.execute_insert(query, (name, description, duration_months,
                                                       price_group, price_individual))
            logger.info(f"Created course {course_id}: {name}")
            return course_id
        except Exception as e:
            logger.error(f"Error creating course: {e}")
            return None