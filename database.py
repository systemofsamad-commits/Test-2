import datetime
import logging
import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

from config import Config
from models.data_models import StudentRegistration

config = Config()
logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.init_db()
        self.migrate_existing_data()

    def init_db(self):
        with self._get_connection() as conn:
            c = conn.cursor()
            # Основная таблица регистраций
            c.execute("""
                      CREATE TABLE IF NOT EXISTS registrations
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          user_id
                          INTEGER
                          NOT
                          NULL,
                          name
                          TEXT
                          NOT
                          NULL,
                          phone
                          TEXT
                          NOT
                          NULL,
                          course
                          TEXT
                          NOT
                          NULL,
                          training_type
                          TEXT
                          NOT
                          NULL,
                          schedule
                          TEXT
                          NOT
                          NULL,
                          price
                          TEXT
                          NOT
                          NULL,
                          status
                          TEXT
                          DEFAULT
                          'active',
                          progress
                          REAL
                          DEFAULT
                          0.0,
                          consultation_time
                          TIMESTAMP
                          NULL,
                          trial_lesson_time
                          TIMESTAMP
                          NULL,
                          lesson_time
                          TIMESTAMP
                          NULL,
                          created_at
                          TIMESTAMP
                          DEFAULT
                          CURRENT_TIMESTAMP,
                          notified
                          BOOLEAN
                          DEFAULT
                          0,
                          reminder_sent
                          BOOLEAN
                          DEFAULT
                          0,
                          current_db
                          TEXT
                          DEFAULT
                          'other',
                          attendance
                          INTEGER
                          DEFAULT
                          0,
                          grade
                          TEXT
                          NULL
                      )
                      """)

            # Таблицы по статусам
            for table in config.TABLE_NAMES.values():
                c.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        phone TEXT NOT NULL,
                        course TEXT NOT NULL,
                        training_type TEXT NOT NULL,
                        schedule TEXT NOT NULL,
                        price TEXT NOT NULL,
                        progress REAL DEFAULT 0.0,
                        consultation_time TIMESTAMP NULL,
                        trial_lesson_time TIMESTAMP NULL,
                        lesson_time TIMESTAMP NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notified BOOLEAN DEFAULT 0,
                        reminder_sent BOOLEAN DEFAULT 0,
                        attendance INTEGER DEFAULT 0,
                        grade TEXT NULL
                    )
                """)

            # Таблица напоминаний
            c.execute("""
                      CREATE TABLE IF NOT EXISTS reminders
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          user_id
                          INTEGER
                          NOT
                          NULL,
                          text
                          TEXT
                          NOT
                          NULL,
                          due_date
                          TIMESTAMP
                          NOT
                          NULL,
                          sent
                          BOOLEAN
                          DEFAULT
                          0
                      )
                      """)

            # Таблица отзывов
            c.execute("""
                      CREATE TABLE IF NOT EXISTS feedback
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          user_id
                          INTEGER
                          NOT
                          NULL,
                          reg_id
                          INTEGER
                          NOT
                          NULL,
                          rating
                          INTEGER
                          NOT
                          NULL,
                          comment
                          TEXT,
                          created_at
                          TIMESTAMP
                          DEFAULT
                          CURRENT_TIMESTAMP
                      )
                      """)
            c.execute("""
                      CREATE TABLE IF NOT EXISTS admins
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          user_id
                          INTEGER
                          UNIQUE
                          NOT
                          NULL,
                          username
                          TEXT,
                          full_name
                          TEXT,
                          created_at
                          TIMESTAMP
                          DEFAULT
                          CURRENT_TIMESTAMP,
                          is_active
                          BOOLEAN
                          DEFAULT
                          1
                      )
                      """)

            # Таблица преподавателей
            c.execute("""
                      CREATE TABLE IF NOT EXISTS teachers
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          name
                          TEXT
                          NOT
                          NULL,
                          phone
                          TEXT
                          NOT
                          NULL,
                          email
                          TEXT,
                          specialization
                          TEXT,
                          experience
                          TEXT,
                          created_at
                          TIMESTAMP
                          DEFAULT
                          CURRENT_TIMESTAMP,
                          is_active
                          BOOLEAN
                          DEFAULT
                          1
                      )
                      """)

            # Таблица курсов
            c.execute("""
                      CREATE TABLE IF NOT EXISTS courses
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          name
                          TEXT
                          NOT
                          NULL
                          UNIQUE,
                          description
                          TEXT,
                          duration
                          TEXT,
                          price
                          TEXT,
                          created_at
                          TIMESTAMP
                          DEFAULT
                          CURRENT_TIMESTAMP,
                          is_active
                          BOOLEAN
                          DEFAULT
                          1
                      )
                      """)

            # Таблица групп
            c.execute("""
                      CREATE TABLE IF NOT EXISTS groups
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          name
                          TEXT
                          NOT
                          NULL
                          UNIQUE,
                          course_id
                          INTEGER,
                          teacher_id
                          INTEGER,
                          schedule
                          TEXT,
                          max_students
                          INTEGER
                          DEFAULT
                          10,
                          current_students
                          INTEGER
                          DEFAULT
                          0,
                          created_at
                          TIMESTAMP
                          DEFAULT
                          CURRENT_TIMESTAMP,
                          is_active
                          BOOLEAN
                          DEFAULT
                          1,
                          FOREIGN
                          KEY
                      (
                          course_id
                      ) REFERENCES courses
                      (
                          id
                      ),
                          FOREIGN KEY
                      (
                          teacher_id
                      ) REFERENCES teachers
                      (
                          id
                      )
                          )
                      """)

            # Таблица уроков
            c.execute("""
                      CREATE TABLE IF NOT EXISTS lessons
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          group_id
                          INTEGER,
                          teacher_id
                          INTEGER,
                          topic
                          TEXT
                          NOT
                          NULL,
                          lesson_date
                          TIMESTAMP
                          NOT
                          NULL,
                          duration_minutes
                          INTEGER
                          DEFAULT
                          60,
                          materials
                          TEXT,
                          homework
                          TEXT,
                          created_at
                          TIMESTAMP
                          DEFAULT
                          CURRENT_TIMESTAMP,
                          FOREIGN
                          KEY
                      (
                          group_id
                      ) REFERENCES groups
                      (
                          id
                      ),
                          FOREIGN KEY
                      (
                          teacher_id
                      ) REFERENCES teachers
                      (
                          id
                      )
                          )
                      """)

            # Таблица студентов (расширяем существующую логику)
            c.execute("""
                      CREATE TABLE IF NOT EXISTS students
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          registration_id
                          INTEGER
                          UNIQUE,
                          group_id
                          INTEGER,
                          name
                          TEXT
                          NOT
                          NULL,
                          phone
                          TEXT
                          NOT
                          NULL,
                          email
                          TEXT,
                          created_at
                          TIMESTAMP
                          DEFAULT
                          CURRENT_TIMESTAMP,
                          is_active
                          BOOLEAN
                          DEFAULT
                          1,
                          FOREIGN
                          KEY
                      (
                          registration_id
                      ) REFERENCES registrations
                      (
                          id
                      ),
                          FOREIGN KEY
                      (
                          group_id
                      ) REFERENCES groups
                      (
                          id
                      )
                          )
                      """)

            # Добавляем начальных администраторов
            for admin_id in config.ADMIN_IDS:
                c.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (admin_id,))

            conn.commit()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        try:
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def move_to_status_table(self, registration_id: int, old_status: str, new_status: str):
        """Переместить запись из одной таблицы статуса в другую"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                old_table = config.TABLE_NAMES.get(old_status, 'registrations_other')
                new_table = config.TABLE_NAMES.get(new_status, 'registrations_other')
                if old_status != new_status:
                    c.execute(f"DELETE FROM {old_table} WHERE id = ?", (registration_id,))
                c.execute(f"""
                    INSERT OR IGNORE INTO {new_table} 
                    (id, user_id, name, phone, course, training_type, schedule, price,
                     progress, consultation_time, trial_lesson_time, lesson_time,
                     created_at, notified, reminder_sent, attendance, grade)
                    SELECT id, user_id, name, phone, course, training_type, schedule, price,
                           progress, consultation_time, trial_lesson_time, lesson_time,
                           created_at, notified, reminder_sent, attendance, grade
                    FROM registrations WHERE id = ?
                """, (registration_id,))
                c.execute("UPDATE registrations SET status = ?, current_db = ? WHERE id = ?",
                          (new_status, new_table.replace('registrations_', ''), registration_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error moving registration {registration_id} to {new_status}: {e}")
            return False

    def save_registration(self, user_id: int, name: str, phone: str, course: str,
                          training_type: str, schedule: str, price: str) -> bool:
        """Сохранение новой регистрации с автоматическим статусом 'active'"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # Вставляем в главную таблицу registrations
                c.execute("""
                          INSERT INTO registrations
                          (user_id, name, phone, course, training_type, schedule, price,
                           status, current_db)
                          VALUES (?, ?, ?, ?, ?, ?, ?, 'active', 'active')
                          """, (user_id, name, phone, course, training_type, schedule, price))

                reg_id = c.lastrowid

                # Сразу вставляем в таблицу registrations_active
                c.execute("""
                          INSERT INTO registrations_active
                              (id, user_id, name, phone, course, training_type, schedule, price)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                          """, (reg_id, user_id, name, phone, course, training_type, schedule, price))

                conn.commit()
                logger.info(f"✅ Новая регистрация: {name} (ID: {reg_id}) - статус: 'active'")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении регистрации: {e}")
            return False

    def get_user_registrations(self, user_id: int) -> List[StudentRegistration]:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          SELECT id,
                                 user_id,
                                 name,
                                 phone,
                                 course,
                                 training_type,
                                 schedule,
                                 price,
                                 status,
                                 consultation_time,
                                 trial_lesson_time,
                                 lesson_time,
                                 created_at,
                                 notified,
                                 reminder_sent,
                                 progress,
                                 attendance,
                                 grade
                          FROM registrations
                          WHERE user_id = ?
                          ORDER BY created_at DESC
                          """, (user_id,))
                rows = c.fetchall()
                return [StudentRegistration(*row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting registrations for user {user_id}: {e}")
            return []

    def get_user_registrations_count(self, user_id: int) -> int:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM registrations WHERE user_id = ? AND status != 'terminated'", (user_id,))
                return c.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting registrations for user {user_id}: {e}")
            return 0

    def save_reminder(self, user_id: int, text: str, due_date: str) -> bool:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("INSERT INTO reminders (user_id, text, due_date) VALUES (?, ?, ?)",
                          (user_id, text, due_date))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving reminder for user {user_id}: {e}")
            return False

    def get_user_reminders(self, user_id: int) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT id, user_id, text, due_date, sent FROM reminders WHERE user_id = ? ORDER BY due_date ASC",
                    (user_id,))
                rows = c.fetchall()
                return [{'id': row[0], 'user_id': row[1], 'text': row[2], 'due_date': row[3], 'sent': bool(row[4])} for
                        row in rows]
        except Exception as e:
            logger.error(f"Error getting reminders for user {user_id}: {e}")
            return []

    def get_active_students(self) -> List[StudentRegistration]:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          SELECT id,
                                 user_id,
                                 name,
                                 phone,
                                 course,
                                 training_type,
                                 schedule,
                                 price,
                                 status,
                                 consultation_time,
                                 trial_lesson_time,
                                 lesson_time,
                                 created_at,
                                 notified,
                                 reminder_sent,
                                 progress,
                                 attendance,
                                 grade
                          FROM registrations
                          WHERE status = 'active'
                          """)
                rows = c.fetchall()
                return [StudentRegistration(*row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting active students: {e}")
            return []

    def get_trial_lessons(self) -> List[StudentRegistration]:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          SELECT id,
                                 user_id,
                                 name,
                                 phone,
                                 course,
                                 training_type,
                                 schedule,
                                 price,
                                 status,
                                 consultation_time,
                                 trial_lesson_time,
                                 lesson_time,
                                 created_at,
                                 notified,
                                 reminder_sent,
                                 progress,
                                 attendance,
                                 grade
                          FROM registrations
                          WHERE status = 'trial'
                            AND trial_lesson_time IS NOT NULL
                          """)
                rows = c.fetchall()
                return [StudentRegistration(*row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting trial lessons: {e}")
            return []

    def update_status(self, registration_id: int, new_status: str) -> bool:
        """
        Обновление статуса регистрации с переносом в соответствующую таблицу
        Использует оптимизированный процесс
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # Получаем текущий статус и данные
                c.execute("""
                          SELECT status,
                                 user_id,
                                 name,
                                 phone,
                                 course,
                                 training_type,
                                 schedule,
                                 price,
                                 progress,
                                 consultation_time,
                                 trial_lesson_time,
                                 lesson_time,
                                 created_at,
                                 notified,
                                 reminder_sent,
                                 attendance,
                                 grade
                          FROM registrations
                          WHERE id = ?
                          """, (registration_id,))

                row = c.fetchone()
                if not row:
                    logger.error(f"❌ Регистрация {registration_id} не найдена")
                    return False

                old_status = row[0]

                # Если статус не изменился - не делаем ничего
                if old_status == new_status:
                    logger.info(f"ℹ️ Статус {registration_id} уже {new_status}")
                    return True

                # Получаем названия таблиц
                old_table = config.TABLE_NAMES.get(old_status, 'registrations_other')
                new_table = config.TABLE_NAMES.get(new_status, 'registrations_other')

                # Распаковываем данные для вставки
                (status, user_id, name, phone, course, training_type, schedule,
                 price, progress, consultation_time, trial_lesson_time, lesson_time,
                 created_at, notified, reminder_sent, attendance, grade) = row

                # Удаляем из старой таблицы
                c.execute(f"DELETE FROM {old_table} WHERE id = ?", (registration_id,))

                # Вставляем в новую таблицу
                c.execute(f"""
                    INSERT OR IGNORE INTO {new_table}
                    (id, user_id, name, phone, course, training_type, schedule, price,
                     progress, consultation_time, trial_lesson_time, lesson_time,
                     created_at, notified, reminder_sent, attendance, grade)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (registration_id, user_id, name, phone, course, training_type,
                      schedule, price, progress, consultation_time, trial_lesson_time,
                      lesson_time, created_at, notified, reminder_sent, attendance, grade))

                # Обновляем главную таблицу
                c.execute("""
                          UPDATE registrations
                          SET status     = ?,
                              current_db = ?
                          WHERE id = ?
                          """, (new_status, new_table.replace('registrations_', ''), registration_id))

                conn.commit()
                config.STATUSES.get(new_status, new_status)
                logger.info(f"✅ Статус {registration_id} обновлен: {old_status} → {new_status}")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении статуса {registration_id}: {e}")
            return False

    def set_trial_lesson_time(self, registration_id: int, lesson_time: str) -> bool:
        """Установить время пробного урока и перевести в статус 'trial'"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # Обновляем в главной таблице
                c.execute("""
                          UPDATE registrations
                          SET trial_lesson_time = ?,
                              status            = 'trial',
                              current_db        = 'trial'
                          WHERE id = ?
                          """, (lesson_time, registration_id))

                # Обновляем/вставляем в таблицу trial
                c.execute(f"""
                    INSERT OR REPLACE INTO registrations_trial
                    SELECT * FROM registrations WHERE id = ?
                """, (registration_id,))

                # Удаляем из старой таблицы если была в active
                c.execute("DELETE FROM registrations_active WHERE id = ?", (registration_id,))

                conn.commit()
                logger.info(f"✅ Пробный урок установлен для {registration_id}: {lesson_time}")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка при установке пробного урока {registration_id}: {e}")
            return False

    def set_consultation_time(self, registration_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE registrations SET consultation_time = CURRENT_TIMESTAMP WHERE id = ?",
                          (registration_id,))
                conn.commit()
                logger.info(f"Set consultation time for {registration_id}")
                return True
        except Exception as e:
            logger.error(f"Error setting consultation time for {registration_id}: {e}")
            return False

    def set_lesson_time(self, registration_id: int, lesson_time: str) -> bool:
        """Установить время начала обучения и перевести в статус 'studying'"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # Обновляем в главной таблице
                c.execute("""
                          UPDATE registrations
                          SET lesson_time = ?,
                              status      = 'studying',
                              current_db  = 'studying'
                          WHERE id = ?
                          """, (lesson_time, registration_id))

                # Обновляем/вставляем в таблицу studying
                c.execute(f"""
                    INSERT OR REPLACE INTO registrations_studying
                    SELECT * FROM registrations WHERE id = ?
                """, (registration_id,))

                # Удаляем из старых таблиц
                c.execute("DELETE FROM registrations_active WHERE id = ?", (registration_id,))
                c.execute("DELETE FROM registrations_trial WHERE id = ?", (registration_id,))

                conn.commit()
                logger.info(f"✅ Обучение начато для {registration_id}: {lesson_time}")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка при установке времени обучения {registration_id}: {e}")
            return False

    def mark_notified(self, registration_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE registrations SET notified = 1 WHERE id = ?", (registration_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error marking notified for {registration_id}: {e}")
            return False

    def mark_reminder_sent(self, registration_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE registrations SET reminder_sent = 1 WHERE id = ?", (registration_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error marking reminder sent for {registration_id}: {e}")
            return False

    def find_by_phone(self, phone: str) -> List[StudentRegistration]:
        try:
            from utils.validators import format_phone
            formatted_phone = format_phone(phone)
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          SELECT id,
                                 user_id,
                                 name,
                                 phone,
                                 course,
                                 training_type,
                                 schedule,
                                 price,
                                 status,
                                 consultation_time,
                                 trial_lesson_time,
                                 lesson_time,
                                 created_at,
                                 notified,
                                 reminder_sent,
                                 progress,
                                 attendance,
                                 grade
                          FROM registrations
                          WHERE phone LIKE ?
                             OR phone LIKE ?
                          ORDER BY created_at DESC
                          """, (f"%{formatted_phone}%", f"%{formatted_phone.replace('+', '')}%"))
                rows = c.fetchall()
                return [StudentRegistration(*row) for row in rows]
        except Exception as e:
            logger.error(f"Error finding by phone {phone}: {e}")
            return []

    def get_students_by_status(self, status: str) -> List[StudentRegistration]:
        """Получить студентов по статусу из соответствующей таблицы"""
        try:
            table_name = config.TABLE_NAMES.get(status, 'registrations_other')

            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute(f"""
                    SELECT id, user_id, name, phone, course, training_type, schedule, 
                           price, NULL as status, consultation_time, trial_lesson_time, 
                           lesson_time, created_at, notified, reminder_sent, progress, 
                           attendance, grade
                    FROM {table_name}
                    ORDER BY created_at DESC
                """)

                rows = c.fetchall()

                # Устанавливаем правильный статус для каждого студента
                result = []
                for row in rows:
                    row_list = list(row)
                    row_list[8] = status  # Устанавливаем статус в правильную позицию
                    result.append(StudentRegistration(*row_list))

                return result

        except Exception as e:
            logger.error(f"❌ Ошибка при получении студентов по статусу '{status}': {e}")
            return []

    def get_all_registrations(self) -> List[StudentRegistration]:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          SELECT id,
                                 user_id,
                                 name,
                                 phone,
                                 course,
                                 training_type,
                                 schedule,
                                 price,
                                 status,
                                 consultation_time,
                                 trial_lesson_time,
                                 lesson_time,
                                 created_at,
                                 notified,
                                 reminder_sent,
                                 progress,
                                 attendance,
                                 grade
                          FROM registrations
                          ORDER BY created_at DESC
                          """)
                rows = c.fetchall()
                return [StudentRegistration(*row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting all registrations: {e}")
            return []

    @staticmethod
    def migrate_existing_data():
        """ОТКЛЮЧЕНО - Больше не используется"""
        logger.info("ℹ️ Migration function disabled - using optimized update_status instead")
        return

    def cleanup_old_registrations(self):
        """Удалить старые данные из таблиц статусов при необходимости"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # Удаляем из таблиц статусов записи которых нет в главной таблице
                for table in config.TABLE_NAMES.values():
                    c.execute(f"""
                        DELETE FROM {table}
                        WHERE id NOT IN (SELECT id FROM registrations)
                    """)

                conn.commit()
                logger.info("✅ Очистка завершена - удалены осиротевшие записи")
                return True

        except Exception as e:
            logger.error(f"❌ Ошибка при очистке данных: {e}")
            return False

    def get_weekly_stats(self) -> Dict:
        """Получить статистику за неделю"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            # Получаем регистрации за последние 7 дней
            cursor.execute("""
                           SELECT COUNT(*)
                           FROM registrations
                           WHERE created_at >= datetime('now', '-7 days')
                           """)
            new_registrations = cursor.fetchone()[0]

            # Завершившие за неделю
            cursor.execute("""
                           SELECT COUNT(*)
                           FROM registrations
                           WHERE status = 'completed'
                             AND updated_at >= datetime('now', '-7 days')
                           """)
            completed = cursor.fetchone()[0]

            # Замороженные за неделю
            cursor.execute("""
                           SELECT COUNT(*)
                           FROM registrations
                           WHERE status = 'frozen'
                             AND updated_at >= datetime('now', '-7 days')
                           """)
            frozen = cursor.fetchone()[0]

            # Начавшие обучение
            cursor.execute("""
                           SELECT COUNT(*)
                           FROM registrations
                           WHERE status = 'studying'
                             AND updated_at >= datetime('now', '-7 days')
                           """)
            started_studying = cursor.fetchone()[0]

            # Статистика по дням недели
            daily_stats = []
            for i in range(7):
                cursor.execute("""
                               SELECT COUNT(*)
                               FROM registrations
                               WHERE DATE (created_at) = DATE ('now', ? || ' days')
                               """, (f'-{6 - i}',))
                daily_stats.append(cursor.fetchone()[0])

            conn.close()

            return {
                'new_registrations': new_registrations,
                'completed': completed,
                'frozen': frozen,
                'started_studying': started_studying,
                'daily': daily_stats
            }

        except Exception as e:
            logger.error(f"Error in get_weekly_stats: {e}")
            return {
                'new_registrations': 0,
                'completed': 0,
                'frozen': 0,
                'started_studying': 0,
                'daily': [0, 0, 0, 0, 0, 0, 0]
            }

    def mark_reminder_sent_db(self, reminder_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE reminders SET sent = 1 WHERE id = ?", (reminder_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error marking reminder sent for {reminder_id}: {e}")
            return False

    def save_feedback(self, user_id: int, user_name: str, feedback_type: str,
                      feedback_text: str, rating: int = None, created_at=None):
        """Сохранить обратную связь"""
        try:
            if created_at is None:
                created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            query = """INSERT INTO feedback
                           (user_id, user_name, feedback_type, feedback_text, rating, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)"""
            return self.execute_query(query, (user_id, user_name, feedback_type,
                                              feedback_text, rating, created_at))
        except Exception as e:
            print(f"Ошибка сохранения отзыва: {e}")
            return False

    def get_feedback_stats(self) -> Dict:
        """Получить статистику обратной связи"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            # Общее количество
            cursor.execute("SELECT COUNT(*) FROM feedback")
            total = cursor.fetchone()[0]

            # По типам
            cursor.execute("SELECT COUNT(*) FROM feedback WHERE feedback_type = 'review'")
            reviews = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM feedback WHERE feedback_type = 'suggestion'")
            suggestions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM feedback WHERE feedback_type = 'issue'")
            issues = cursor.fetchone()[0]

            # Средняя оценка
            cursor.execute("SELECT AVG(rating) FROM feedback WHERE rating IS NOT NULL")
            result = cursor.fetchone()
            avg_rating = result[0] if result[0] else 0

            # Распределение оценок
            rating_distribution = {}
            for rating in range(1, 6):
                cursor.execute("SELECT COUNT(*) FROM feedback WHERE rating = ?", (rating,))
                rating_distribution[rating] = cursor.fetchone()[0]

            conn.close()

            return {
                'total': total,
                'reviews': reviews,
                'suggestions': suggestions,
                'issues': issues,
                'avg_rating': avg_rating,
                'rating_distribution': rating_distribution
            }

        except Exception as e:
            logger.error(f"Error in get_feedback_stats: {e}")
            return {
                'total': 0,
                'reviews': 0,
                'suggestions': 0,
                'issues': 0,
                'avg_rating': 0,
                'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }

    def update_progress(self, reg_id: int, progress: float) -> bool:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE registrations SET progress = ? WHERE id = ?", (progress, reg_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating progress for {reg_id}: {e}")
            return False

    def update_attendance(self, reg_id: int, attendance: int) -> bool:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE registrations SET attendance = ? WHERE id = ?", (attendance, reg_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating attendance for {reg_id}: {e}")
            return False

    def update_grade(self, reg_id: int, grade: str) -> bool:
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE registrations SET grade = ? WHERE id = ?", (grade, reg_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating grade for {reg_id}: {e}")
            return False

    def get_student_by_id(self, reg_id: int) -> Optional[StudentRegistration]:
        """Получить студента по ID"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          SELECT id,
                                 user_id,
                                 name,
                                 phone,
                                 course,
                                 training_type,
                                 schedule,
                                 price,
                                 status,
                                 consultation_time,
                                 trial_lesson_time,
                                 lesson_time,
                                 created_at,
                                 notified,
                                 reminder_sent,
                                 progress,
                                 attendance,
                                 grade
                          FROM registrations
                          WHERE id = ?
                          """, (reg_id,))
                row = c.fetchone()
                if row:
                    processed_row = []
                    for value in row:
                        if value is None:
                            processed_row.append("")
                        else:
                            processed_row.append(value)
                    processed_row[13] = bool(processed_row[13])  # notified
                    processed_row[14] = bool(processed_row[14])  # reminder_sent
                    return StudentRegistration(*processed_row)
                return None
        except Exception as e:
            logger.error(f"Error getting student by ID {reg_id}: {e}")
            return None

    # НОВЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С АДМИНИСТРАТОРАМИ

    def add_admin(self, user_id: int, username: str = None, full_name: str = None) -> bool:
        """Добавить администратора"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("""
                           INSERT INTO admins (user_id, username, full_name, is_active)
                           VALUES (?, ?, ?, 1)
                           """, (user_id, username, full_name))

            conn.commit()
            conn.close()

            logger.info(f"✅ Admin added: {user_id}")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"⚠️ Admin {user_id} already exists")
            return False
        except Exception as e:
            logger.error(f"❌ Error adding admin: {e}")
            return False

    def remove_admin(self, user_id: int) -> bool:
        """Удалить администратора"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))

            conn.commit()
            affected = cursor.rowcount
            conn.close()

            if affected > 0:
                logger.info(f"✅ Admin removed: {user_id}")
                return True
            else:
                logger.warning(f"⚠️ Admin {user_id} not found")
                return False

        except Exception as e:
            logger.error(f"❌ Error removing admin: {e}")
            return False

    def get_all_admins(self) -> List[Dict]:
        """Получить список всех администраторов"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("""
                           SELECT id, user_id, username, full_name, created_at, is_active
                           FROM admins
                           ORDER BY created_at DESC
                           """)

            rows = cursor.fetchall()
            conn.close()

            admins = []
            for row in rows:
                admins.append({
                    'id': row[0],
                    'user_id': row[1],
                    'username': row[2],
                    'full_name': row[3],
                    'created_at': row[4],
                    'is_active': row[5]
                })

            return admins

        except Exception as e:
            logger.error(f"❌ Error getting admins: {e}")
            return []

    def is_admin(self, user_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("""
                           SELECT COUNT(*)
                           FROM admins
                           WHERE user_id = ?
                             AND is_active = 1
                           """, (user_id,))

            count = cursor.fetchone()[0]
            conn.close()

            return count > 0

        except Exception as e:
            logger.error(f"❌ Error checking admin status: {e}")
            return False

    def update_admin_status(self, user_id: int, is_active: bool) -> bool:
        """Обновить статус администратора (активен/неактивен)"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("""
                           UPDATE admins
                           SET is_active = ?
                           WHERE user_id = ?
                           """, (1 if is_active else 0, user_id))

            conn.commit()
            affected = cursor.rowcount
            conn.close()

            if affected > 0:
                status = "activated" if is_active else "deactivated"
                logger.info(f"✅ Admin {user_id} {status}")
                return True
            else:
                logger.warning(f"⚠️ Admin {user_id} not found")
                return False

        except Exception as e:
            logger.error(f"❌ Error updating admin status: {e}")
            return False

    def get_total_students_count(self) -> int:
        """Получить общее количество студентов"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM registrations")
            count = cursor.fetchone()[0]

            conn.close()
            return count

        except Exception as e:
            logger.error(f"❌ Error getting students count: {e}")
            return 0

    def get_students_count_by_status(self, status: str) -> int:
        """Получить количество студентов по статусу"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM registrations WHERE status = ?", (status,))
            count = cursor.fetchone()[0]

            conn.close()
            return count

        except Exception as e:
            logger.error(f"❌ Error getting students count by status: {e}")
            return 0

    def get_students_by_course(self, course: str) -> List:
        """Получить список студентов по курсу"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("""
                           SELECT *
                           FROM registrations
                           WHERE course = ?
                           ORDER BY created_at DESC
                           """, (course,))

            rows = cursor.fetchall()
            conn.close()

            # Преобразуем в объекты StudentRegistration
            from data_models import StudentRegistration
            students = []
            for row in rows:
                students.append(StudentRegistration(
                    id=row[0],
                    user_id=row[1],
                    name=row[2],
                    phone=row[3],
                    course=row[4],
                    training_type=row[5],
                    schedule=row[6],
                    price=row[7],
                    status=row[8],
                    created_at=row[9],
                    progress=row[10] if len(row) > 10 else 0.0,
                    trial_lesson_time=row[11] if len(row) > 11 else None
                ))

            return students

        except Exception as e:
            logger.error(f"❌ Error getting students by course: {e}")
            return []

    def get_monthly_registrations(self) -> Dict:
        """Получить статистику регистраций по месяцам"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("""
                           SELECT strftime('%Y-%m', created_at) as month,
                    COUNT(*) as count
                           FROM registrations
                           GROUP BY month
                           ORDER BY month DESC
                               LIMIT 12
                           """)

            rows = cursor.fetchall()
            conn.close()

            monthly_data = {}
            for row in rows:
                monthly_data[row[0]] = row[1]

            return monthly_data

        except Exception as e:
            logger.error(f"❌ Error getting monthly registrations: {e}")
            return {}

    # НОВЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С ПРЕПОДАВАТЕЛЯМИ

    def add_teacher(self, name: str, phone: str, email: str = None,
                    specialization: str = None, experience: str = None) -> bool:
        """Добавить преподавателя"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          INSERT INTO teachers (name, phone, email, specialization, experience)
                          VALUES (?, ?, ?, ?, ?)
                          """, (name, phone, email, specialization, experience))
                conn.commit()
                logger.info(f"Added teacher: {name}")
                return True
        except Exception as e:
            logger.error(f"Error adding teacher {name}: {e}")
            return False

    def get_all_teachers(self) -> List[Dict]:
        """Получить список всех преподавателей"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          SELECT id,
                                 name,
                                 phone,
                                 email,
                                 specialization,
                                 experience,
                                 created_at,
                                 is_active
                          FROM teachers
                          ORDER BY name
                          """)
                rows = c.fetchall()
                return [{
                    'id': row[0],
                    'name': row[1],
                    'phone': row[2],
                    'email': row[3],
                    'specialization': row[4],
                    'experience': row[5],
                    'created_at': row[6],
                    'is_active': bool(row[7])
                } for row in rows]
        except Exception as e:
            logger.error(f"Error getting teachers: {e}")
            return []

    def remove_teacher(self, teacher_id: int) -> bool:
        """Удалить преподавателя"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE teachers SET is_active = 0 WHERE id = ?", (teacher_id,))
                conn.commit()
                logger.info(f"Removed teacher: id {teacher_id}")
                return True
        except Exception as e:
            logger.error(f"Error removing teacher {teacher_id}: {e}")
            return False

    def add_course(self, name: str, description: str = None, duration: str = None, price: str = None) -> bool:
        """Добавить курс"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          INSERT INTO courses (name, description, duration, price)
                          VALUES (?, ?, ?, ?)
                          """, (name, description, duration, price))
                conn.commit()
                logger.info(f"Added course: {name}")
                return True
        except Exception as e:
            logger.error(f"Error adding course {name}: {e}")
            return False

    def get_all_courses(self) -> List[Dict]:
        """Получить список всех курсов"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          SELECT id, name, description, duration, price, created_at
                          FROM courses
                          WHERE is_active = 1
                          ORDER BY name
                          """)
                rows = c.fetchall()
                return [{
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'duration': row[3],
                    'price': row[4],
                    'created_at': row[5]
                } for row in rows]
        except Exception as e:
            logger.error(f"Error getting courses: {e}")
            return []

    def remove_course(self, course_id):
        """Удаление курса (помечаем как неактивный)"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE courses SET is_active = 0 WHERE id = ?", (course_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error removing course: {e}")
            return False

    def add_group(self, name: str, course_id: int, teacher_id: int, schedule: str,
                  max_students: int = 10) -> bool:
        """Добавить группу"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          INSERT INTO groups (name, course_id, teacher_id, schedule, max_students)
                          VALUES (?, ?, ?, ?, ?)
                          """, (name, course_id, teacher_id, schedule, max_students))
                conn.commit()
                logger.info(f"Added group: {name}")
                return True
        except Exception as e:
            logger.error(f"Error adding group {name}: {e}")
            return False

    def get_all_groups(self) -> List[Dict]:
        """Получить список всех групп"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          SELECT g.id,
                                 g.name,
                                 g.course_id,
                                 c.name as course_name,
                                 g.teacher_id,
                                 t.name as teacher_name,
                                 g.schedule,
                                 g.max_students,
                                 g.current_students,
                                 g.created_at,
                                 g.is_active
                          FROM groups g
                                   LEFT JOIN courses c ON g.course_id = c.id
                                   LEFT JOIN teachers t ON g.teacher_id = t.id
                          WHERE g.is_active = 1
                          ORDER BY g.name
                          """)
                rows = c.fetchall()
                return [{
                    'id': row[0],
                    'name': row[1],
                    'course_id': row[2],
                    'course_name': row[3],
                    'teacher_id': row[4],
                    'teacher_name': row[5],
                    'schedule': row[6],
                    'max_students': row[7],
                    'current_students': row[8],
                    'created_at': row[9],
                    'is_active': bool(row[10])
                } for row in rows]
        except Exception as e:
            logger.error(f"Error getting groups: {e}")
            return []

    def remove_group(self, group_id: int) -> bool:
        """Удалить группу (пометить как неактивную)"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE groups SET is_active = 0 WHERE id = ?", (group_id,))
                conn.commit()
                logger.info(f"Removed group: id {group_id}")
                return True
        except Exception as e:
            logger.error(f"Error removing group {group_id}: {e}")
            return False

    def get_active_courses(self) -> List[Dict]:
        """Получить список активных курсов для выбора"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT id, name FROM courses WHERE is_active = 1 ORDER BY name")
                rows = c.fetchall()
                return [{'id': row[0], 'name': row[1]} for row in rows]
        except Exception as e:
            logger.error(f"Error getting active courses: {e}")
            return []

    def get_active_teachers(self) -> List[Dict]:
        """Получить список активных преподавателей для выбора"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT id, name FROM teachers WHERE is_active = 1 ORDER BY name")
                rows = c.fetchall()
                return [{'id': row[0], 'name': row[1]} for row in rows]
        except Exception as e:
            logger.error(f"Error getting active teachers: {e}")
            return []

    def add_student(self, registration_id: int, group_id: int = None) -> bool:
        """Добавить студента (на основе регистрации)"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()

                # Получаем данные регистрации
                c.execute("""
                          SELECT user_id, name, phone
                          FROM registrations
                          WHERE id = ?
                          """, (registration_id,))
                reg_data = c.fetchone()

                if not reg_data:
                    return False

                user_id, name, phone = reg_data

                # Добавляем студента
                c.execute("""
                          INSERT INTO students (registration_id, group_id, name, phone)
                          VALUES (?, ?, ?, ?)
                          """, (registration_id, group_id, name, phone))

                # Обновляем счетчик студентов в группе
                if group_id:
                    c.execute("""
                              UPDATE groups
                              SET current_students = current_students + 1
                              WHERE id = ?
                              """, (group_id,))

                conn.commit()
                logger.info(f"Added student: {name} (reg_id: {registration_id})")
                return True
        except Exception as e:
            logger.error(f"Error adding student for registration {registration_id}: {e}")
            return False

    def get_all_students(self) -> List[Dict]:
        """Получить список всех студентов"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          SELECT s.id,
                                 s.registration_id,
                                 s.group_id,
                                 g.name as group_name,
                                 s.name,
                                 s.phone,
                                 s.email,
                                 s.created_at,
                                 s.is_active
                          FROM students s
                                   LEFT JOIN groups g ON s.group_id = g.id
                          WHERE s.is_active = 1
                          ORDER BY s.name
                          """)
                rows = c.fetchall()
                return [{
                    'id': row[0],
                    'registration_id': row[1],
                    'group_id': row[2],
                    'group_name': row[3],
                    'name': row[4],
                    'phone': row[5],
                    'email': row[6],
                    'created_at': row[7],
                    'is_active': bool(row[8])
                } for row in rows]
        except Exception as e:
            logger.error(f"Error getting students: {e}")
            return []

    def remove_student(self, student_id: int) -> bool:
        """Удалить студента (пометить как неактивного)"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("UPDATE students SET is_active = 0 WHERE id = ?", (student_id,))
                conn.commit()
                logger.info(f"Removed student: id {student_id}")
                return True
        except Exception as e:
            logger.error(f"Error removing student {student_id}: {e}")
            return False

    def add_lesson(self, group_id: int, teacher_id: int, topic: str, lesson_date: str,
                   duration_minutes: int = 60, materials: str = None, homework: str = None) -> bool:
        """Добавить урок"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          INSERT INTO lessons (group_id, teacher_id, topic, lesson_date,
                                               duration_minutes, materials, homework)
                          VALUES (?, ?, ?, ?, ?, ?, ?)
                          """, (group_id, teacher_id, topic, lesson_date, duration_minutes, materials, homework))
                conn.commit()
                logger.info(f"Added lesson: {topic} for group {group_id}")
                return True
        except Exception as e:
            logger.error(f"Error adding lesson {topic}: {e}")
            return False

    def get_all_lessons(self) -> List[Dict]:
        """Получить список всех уроков"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          SELECT l.id,
                                 l.group_id,
                                 g.name as group_name,
                                 l.teacher_id,
                                 t.name as teacher_name,
                                 l.topic,
                                 l.lesson_date,
                                 l.duration_minutes,
                                 l.materials,
                                 l.homework,
                                 l.created_at
                          FROM lessons l
                                   LEFT JOIN groups g ON l.group_id = g.id
                                   LEFT JOIN teachers t ON l.teacher_id = t.id
                          ORDER BY l.lesson_date DESC
                          """)
                rows = c.fetchall()
                return [{
                    'id': row[0],
                    'group_id': row[1],
                    'group_name': row[2],
                    'teacher_id': row[3],
                    'teacher_name': row[4],
                    'topic': row[5],
                    'lesson_date': row[6],
                    'duration_minutes': row[7],
                    'materials': row[8],
                    'homework': row[9],
                    'created_at': row[10]
                } for row in rows]
        except Exception as e:
            logger.error(f"Error getting lessons: {e}")
            return []

    def remove_lesson(self, lesson_id: int) -> bool:
        """Удалить урок"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
                conn.commit()
                logger.info(f"Removed lesson: id {lesson_id}")
                return True
        except Exception as e:
            logger.error(f"Error removing lesson {lesson_id}: {e}")
            return False

    def get_active_groups(self) -> List[Dict]:
        """Получить список активных групп для выбора"""
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute("""
                          SELECT id, name
                          FROM groups
                          WHERE is_active = 1
                          ORDER BY name
                          """)
                rows = c.fetchall()
                return [{'id': row[0], 'name': row[1]} for row in rows]
        except Exception as e:
            logger.error(f"Error getting active groups: {e}")
            return []

    def execute_query(self, query, param):
        pass

    def get_student_by_registration_id(self, registration_id):
        pass

    def update_student_trial_date(self, registration_id, text):
        pass

    def update_student_progress(self, registration_id, progress_text):
        pass
