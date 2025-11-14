"""
Все репозитории для базы данных
Содержит: Students, Teachers, Courses, Groups, Admins, Lessons, Feedback, Reminders
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class FeedbackRepository:
    """Репозиторий для работы с отзывами"""

    def __init__(self, db):
        self.db = db

    def create(self, user_id: int, rating: int, comment: Optional[str] = None,
               registration_id: Optional[int] = None, course_id: Optional[int] = None,
               teacher_id: Optional[int] = None) -> Optional[int]:
        """Создать отзыв"""
        try:
            query = """
                    INSERT INTO feedback (user_id, registration_id, course_id, teacher_id,
                                          rating, comment)
                    VALUES (?, ?, ?, ?, ?, ?) 
                    """
            feedback_id = self.db.execute_insert(query, (user_id, registration_id,
                                                         course_id, teacher_id,
                                                         rating, comment))
            logger.info(f"Created feedback {feedback_id} from user {user_id}")
            return feedback_id
        except Exception as e:
            logger.error(f"Error creating feedback: {e}")
            return None

    def get_by_course(self, course_id: int) -> List[Dict]:
        """Получить отзывы по курсу"""
        query = """
                SELECT f.*, u.full_name
                FROM feedback f
                         JOIN users u ON f.user_id = u.id
                WHERE f.course_id = ?
                ORDER BY f.created_at DESC 
                """
        return self.db.execute_query(query, (course_id,))
