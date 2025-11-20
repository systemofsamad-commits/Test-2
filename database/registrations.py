"""
Registration Repository - ИСПРАВЛЕННАЯ ВЕРСИЯ
Репозиторий для работы с регистрациями студентов
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class RegistrationRepository:
    """Репозиторий для работы с регистрациями"""

    def __init__(self, db):
        self.db = db

    def create(self, user_id: int, course_id: int,
               full_name: str, phone: str,  # ✅ ДОБАВЛЕНО: обязательные поля
               training_type_id: Optional[int] = None,
               schedule_id: Optional[int] = None,
               status: str = 'trial') -> Optional[int]:  # ✅ ИСПРАВЛЕНО: 'trial' по умолчанию
        """
        ✅ ИСПРАВЛЕНО: Создать новую регистрацию

        Args:
            user_id: ID пользователя
            course_id: ID курса
            full_name: ФИО студента (ОБЯЗАТЕЛЬНО!)
            phone: Телефон студента (ОБЯЗАТЕЛЬНО!)
            training_type_id: ID типа обучения
            schedule_id: ID расписания
            status: Статус регистрации (по умолчанию 'trial')

        Returns:
            Optional[int]: ID новой регистрации или None при ошибке
        """
        try:
            query = """
                    INSERT INTO registrations
                    (user_id, course_id, full_name, phone, training_type_id, schedule_id, status_code)
                    VALUES (?, ?, ?, ?, ?, ?, ?) \
                    """

            reg_id = self.db.execute_insert(query, (
                user_id,
                course_id,
                full_name,
                phone,
                training_type_id,
                schedule_id,
                status
            ))

            if reg_id:
                logger.info(f"✅ Created registration {reg_id} for user {user_id}")
            else:
                logger.error(f"❌ Failed to create registration for user {user_id}")

            return reg_id

        except Exception as e:
            logger.error(f"❌ Error creating registration: {e}", exc_info=True)
            return None

    def get_by_id(self, reg_id: int) -> Optional[Dict]:
        """
        Получить регистрацию по ID

        Args:
            reg_id: ID регистрации

        Returns:
            Dict: Данные регистрации или None
        """

        def get_by_id(self, reg_id: int) -> Optional[Dict]:
            """
            Получить регистрацию по ID

            ✅ ИСПРАВЛЕНО: Теперь берём full_name и phone из registrations, а не из users
            """
            query = """
                    SELECT r.*,
                           r.full_name as name, -- ✅ Из registrations
                           r.phone,             -- ✅ Из registrations
                           u.telegram_id,
                           c.name      as course,
                           tt.name     as training_type,
                           s.name      as schedule,
                           ss.name     as status_name,
                           CASE
                               WHEN c.price_group IS NOT NULL AND tt.name LIKE '%Группов%'
                                   THEN c.price_group
                               WHEN c.price_individual IS NOT NULL
                                   THEN c.price_individual
                               ELSE 0
                               END     as price
                    FROM registrations r
                             JOIN users u ON r.user_id = u.id
                             JOIN courses c ON r.course_id = c.id
                             LEFT JOIN training_types tt ON r.training_type_id = tt.id
                             LEFT JOIN schedules s ON r.schedule_id = s.id
                             LEFT JOIN student_statuses ss ON r.status_code = ss.code
                    WHERE r.id = ? \
                    """
            rows = self.db.execute_query(query, (reg_id,))
            return rows[0] if rows else None

    def get_by_status(self, status: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Получить регистрации по статусу
        """
        query = """
                SELECT r.*,
                       r.full_name as name,
                       r.phone,
                       c.name      as course,
                       tt.name     as training_type,
                       s.name      as schedule
                FROM registrations r
                         JOIN users u ON r.user_id = u.id
                         JOIN courses c ON r.course_id = c.id
                         LEFT JOIN training_types tt ON r.training_type_id = tt.id
                         LEFT JOIN schedules s ON r.schedule_id = s.id
                WHERE r.status_code = ?
                ORDER BY r.created_at DESC \
                """

        if limit:
            query += f" LIMIT {limit}"

        return self.db.execute_query(query, (status,))

    def get_by_user(self, user_id: int) -> List[Dict]:
        """
        ✅ ИСПРАВЛЕНО: Получить все регистрации пользователя
        """
        query = """
                SELECT r.*,
                       r.full_name as name,
                       r.phone,
                       c.name      as course,
                       tt.name     as training_type,
                       s.name      as schedule,
                       ss.name     as status_name
                FROM registrations r
                         JOIN courses c ON r.course_id = c.id
                         LEFT JOIN training_types tt ON r.training_type_id = tt.id
                         LEFT JOIN schedules s ON r.schedule_id = s.id
                         LEFT JOIN student_statuses ss ON r.status_code = ss.code
                WHERE r.user_id = ?
                ORDER BY r.created_at DESC \
                """
        return self.db.execute_query(query, (user_id,))

    def update_status(self, reg_id: int, new_status: str) -> bool:
        """
        Обновить статус регистрации
        """
        try:
            query = """
                    UPDATE registrations
                    SET status_code = ?,
                        updated_at  = CURRENT_TIMESTAMP
                    WHERE id = ? \
                    """
            rows_affected = self.db.execute_update(query, (new_status, reg_id))

            if rows_affected > 0:
                logger.info(f"✅ Updated registration {reg_id} status to {new_status}")
                return True
            else:
                logger.warning(f"⚠️ Registration {reg_id} not found")
                return False

        except Exception as e:
            logger.error(f"❌ Error updating registration status: {e}", exc_info=True)
            return False

    def get_all(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Получить все регистрации
        """
        query = """
                SELECT r.*,
                       r.full_name as name,
                       r.phone,
                       u.telegram_id,
                       c.name      as course,
                       tt.name     as training_type,
                       s.name      as schedule,
                       ss.name     as status_name
                FROM registrations r
                         JOIN users u ON r.user_id = u.id
                         JOIN courses c ON r.course_id = c.id
                         LEFT JOIN training_types tt ON r.training_type_id = tt.id
                         LEFT JOIN schedules s ON r.schedule_id = s.id
                         LEFT JOIN student_statuses ss ON r.status_code = ss.code
                ORDER BY r.created_at DESC \
                """

        if limit:
            query += f" LIMIT {limit}"

        return self.db.execute_query(query)

    def set_trial_lesson_time(self, reg_id: int, lesson_time: str) -> bool:
        """
        Назначить время пробного урока

        Args:
            reg_id: ID регистрации
            lesson_time: Время урока (строка или datetime)

        Returns:
            bool: True если успешно
        """
        try:
            query = """
                    UPDATE registrations
                    SET trial_lesson_time = ?,
                        updated_at        = CURRENT_TIMESTAMP
                    WHERE id = ? \
                    """
            affected = self.db.execute_update(query, (lesson_time, reg_id))

            if affected > 0:
                logger.info(f"Set trial lesson time for registration {reg_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error setting trial lesson time: {e}")
            return False

    def set_consultation_time(self, reg_id: int, consult_time: str) -> bool:
        """Назначить время консультации"""
        try:
            query = """
                    UPDATE registrations
                    SET consultation_time = ?,
                        updated_at        = CURRENT_TIMESTAMP
                    WHERE id = ? \
                    """
            affected = self.db.execute_update(query, (consult_time, reg_id))
            return affected > 0
        except Exception as e:
            logger.error(f"Error setting consultation time: {e}")
            return False

    def mark_notified(self, reg_id: int) -> bool:
        """Отметить что уведомление отправлено"""
        try:
            query = "UPDATE registrations SET notified = 1 WHERE id = ?"
            affected = self.db.execute_update(query, (reg_id,))
            return affected > 0
        except Exception as e:
            logger.error(f"Error marking as notified: {e}")
            return False

    def mark_reminder_sent(self, reg_id: int) -> bool:
        """Отметить что напоминание отправлено"""
        try:
            query = "UPDATE registrations SET reminder_sent = 1 WHERE id = ?"
            affected = self.db.execute_update(query, (reg_id,))
            return affected > 0
        except Exception as e:
            logger.error(f"Error marking reminder sent: {e}")
            return False

    def get_upcoming_trials(self, days: int = 7) -> List[Dict]:
        """
        Получить предстоящие пробные уроки

        Args:
            days: Количество дней вперед

        Returns:
            List[Dict]: Список регистраций с пробными уроками
        """
        query = """
                SELECT r.*,
                       r.full_name as name,
                       r.phone,
                       u.telegram_id,
                       c.name      as course
                FROM registrations r
                         JOIN users u ON r.user_id = u.id
                         JOIN courses c ON r.course_id = c.id
                WHERE r.trial_lesson_time IS NOT NULL
                  AND r.trial_lesson_time BETWEEN datetime('now')
                    AND datetime('now', '+' || ? || ' days')
                  AND r.reminder_sent = 0
                ORDER BY r.trial_lesson_time \
                """
        return self.db.execute_query(query, (days,))

    def get_stats_by_status(self) -> Dict[str, int]:
        """
        Получить статистику по статусам

        Returns:
            Dict: Статистика {status: count}
        """
        query = """
                SELECT status_code, COUNT(*) as count
                FROM registrations
                GROUP BY status_code \
                """
        rows = self.db.execute_query(query)
        return {row['status_code']: row['count'] for row in rows}

    def delete(self, reg_id: int) -> bool:
        """
        Удалить регистрацию
        """
        try:
            query = "DELETE FROM registrations WHERE id = ?"
            rows_affected = self.db.execute_update(query, (reg_id,))

            if rows_affected > 0:
                logger.info(f"✅ Deleted registration {reg_id}")
                return True
            else:
                logger.warning(f"⚠️ Registration {reg_id} not found")
                return False

        except Exception as e:
            logger.error(f"❌ Error deleting registration: {e}", exc_info=True)
            return False

    def count_by_status(self, status: str) -> int:
        """
        Подсчитать количество регистраций по статусу
        """
        query = "SELECT COUNT(*) as count FROM registrations WHERE status_code = ?"
        rows = self.db.execute_query(query, (status,))
        return rows[0]['count'] if rows else 0

    def get_recent(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """
        Получить недавние регистрации
        """
        query = """
               SELECT r.*, 
                      r.full_name as name, 
                      r.phone, 
                      c.name as course,
                      ss.name as status_name
               FROM registrations r
               JOIN courses c ON r.course_id = c.id
               LEFT JOIN student_statuses ss ON r.status_code = ss.code
               WHERE r.created_at >= datetime('now', '-{} days')
               ORDER BY r.created_at DESC
               LIMIT ?
           """.format(days)

        return self.db.execute_query(query, (limit,))

    def add_note(self, reg_id: int, note: str) -> bool:
        """Добавить заметку к регистрации"""
        try:
            # Получаем существующие заметки
            query = "SELECT notes FROM registrations WHERE id = ?"
            rows = self.db.execute_query(query, (reg_id,))

            if not rows:
                return False

            existing_notes = rows[0].get('notes', '')
            new_notes = f"{existing_notes}\n{note}" if existing_notes else note

            # Обновляем
            query = "UPDATE registrations SET notes = ? WHERE id = ?"
            affected = self.db.execute_update(query, (new_notes, reg_id))
            return affected > 0
        except Exception as e:
            logger.error(f"Error adding note: {e}")
            return False
