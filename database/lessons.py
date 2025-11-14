"""
Все репозитории для базы данных
Содержит: Students, Teachers, Courses, Groups, Admins, Lessons, Feedback, Reminders
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class LessonRepository:
    """Репозиторий для работы с уроками"""

    def __init__(self, db):
        self.db = db

    def create(self, group_id: int, teacher_id: int, topic: str,
               lesson_date: str, duration_minutes: int = 60,
               materials: Optional[str] = None, homework: Optional[str] = None) -> Optional[int]:
        """Создать урок"""
        try:
            query = """
                    INSERT INTO lessons (group_id, teacher_id, topic, lesson_date,
                                         duration_minutes, materials, homework)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """
            lesson_id = self.db.execute_insert(query, (group_id, teacher_id, topic,
                                                       lesson_date, duration_minutes,
                                                       materials, homework))
            logger.info(f"Created lesson {lesson_id}: {topic}")
            return lesson_id
        except Exception as e:
            logger.error(f"Error creating lesson: {e}")
            return None

    def get_by_group(self, group_id: int) -> List[Dict]:
        """Получить уроки группы"""
        query = """
                SELECT l.*, t.name as teacher_name
                FROM lessons l
                         JOIN teachers t ON l.teacher_id = t.id
                WHERE l.group_id = ?
                ORDER BY l.lesson_date DESC
                """
        return self.db.execute_query(query, (group_id,))

    def mark_attendance(self, lesson_id: int, student_id: int,
                        status: str = 'present', notes: Optional[str] = None) -> bool:
        """Отметить посещаемость"""
        try:
            query = """
                    INSERT INTO attendance (lesson_id, student_id, status, notes)
                    VALUES (?, ?, ?, ?) ON CONFLICT(lesson_id, student_id) DO 
                    UPDATE SET
                        status = excluded.status, 
                        notes = excluded.notes 
                    """
            self.db.execute_insert(query, (lesson_id, student_id, status, notes))
            return True
        except Exception as e:
            logger.error(f"Error marking attendance: {e}")
            return False