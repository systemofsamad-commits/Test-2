"""
Все репозитории для базы данных
Содержит: Students, Teachers, Courses, Groups, Admins, Lessons, Feedback, Reminders
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class GroupRepository:
    """Репозиторий для работы с группами"""

    def __init__(self, db):
        self.db = db

    def create(self, name: str, course_id: int, teacher_id: Optional[int] = None,
               schedule_id: Optional[int] = None, max_students: int = 10) -> Optional[int]:
        """Создать группу"""
        try:
            query = """
                    INSERT INTO groups (name, course_id, teacher_id, schedule_id, max_students)
                    VALUES (?, ?, ?, ?, ?)
                    """
            group_id = self.db.execute_insert(query, (name, course_id, teacher_id,
                                                      schedule_id, max_students))
            logger.info(f"Created group {group_id}: {name}")
            return group_id
        except Exception as e:
            logger.error(f"Error creating group: {e}")
            return None

    def get_all_active(self) -> List[Dict]:
        """Получить все активные группы"""
        query = """
                SELECT g.*, 
                       c.name as course_name, 
                       t.name as teacher_name,
                       s.name as schedule_name
                FROM groups g
                         JOIN courses c ON g.course_id = c.id
                         LEFT JOIN teachers t ON g.teacher_id = t.id
                         LEFT JOIN schedules s ON g.schedule_id = s.id
                WHERE g.is_active = 1
                ORDER BY g.name 
                """
        return self.db.execute_query(query)

    def get_by_id(self, group_id: int) -> Optional[Dict]:
        """Получить группу по ID"""
        query = """
                SELECT g.*, 
                       c.name as course_name, 
                       t.name as teacher_name,
                       s.name as schedule_name
                FROM groups g
                         JOIN courses c ON g.course_id = c.id
                         LEFT JOIN teachers t ON g.teacher_id = t.id
                         LEFT JOIN schedules s ON g.schedule_id = s.id
                WHERE g.id = ? 
                """
        rows = self.db.execute_query(query, (group_id,))
        return rows[0] if rows else None

    def get_students(self, group_id: int) -> List[Dict]:
        """Получить студентов группы"""
        query = """
                SELECT s.*, u.full_name, u.phone, sg.enrolled_at
                FROM student_groups sg
                         JOIN students s ON sg.student_id = s.id
                         JOIN users u ON s.user_id = u.id
                WHERE sg.group_id = ? 
                  AND sg.status = 'active'
                ORDER BY u.full_name 
                """
        return self.db.execute_query(query, (group_id,))

    def update_student_count(self, group_id: int) -> bool:
        """Обновить счетчик студентов в группе"""
        try:
            query = """
                    UPDATE groups
                    SET current_students = (SELECT COUNT(*) 
                                            FROM student_groups 
                                            WHERE group_id = ? 
                                              AND status = 'active')
                    WHERE id = ? 
                    """
            affected = self.db.execute_update(query, (group_id, group_id))
            return affected > 0
        except Exception as e:
            logger.error(f"Error updating student count: {e}")
            return False