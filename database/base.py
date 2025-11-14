"""
Base database Class
Базовый класс для работы с SQLite
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import List, Dict, Any

from handlers.user_handlers import db

logger = logging.getLogger(__name__)


def _init_reference_data(cursor):
    """Инициализировать справочные данные"""
    # Статусы
    statuses = [
        ('active', 'Активные', 'Активно проходят обучение'),
        ('trial', 'Пробный урок', 'Записаны на пробный урок'),
        ('studying', 'Обучаются', 'Проходят полный курс'),
        ('frozen', 'Заморожены', 'Временно приостановили обучение'),
        ('waiting_payment', 'Ожидание оплаты', 'Ожидают оплату за курс'),
        ('completed', 'Завершили', 'Успешно завершили курс')
    ]
    cursor.executemany("""
                       INSERT
                           OR IGNORE
                       INTO student_statuses (code, name, description)
                       VALUES (?, ?, ?)
                       """, statuses)

    # Типы обучения
    training_types = [
        ('Групповые занятия (80 минут)', 'Занятия в группе до 10 человек'),
        ('Индивидуальное обучение (1 час)', 'Индивидуальные занятия'),
        ('Групповые занятия (60 минут)', 'Занятия в группе до 15 человек')
    ]
    cursor.executemany("""
                       INSERT
                           OR IGNORE
                       INTO training_types (name, description)
                       VALUES (?, ?)
                       """, training_types)

    # Расписания
    schedules = [
        ('Утренняя группа', '09:00', '11:00'),
        ('Обеденная группа', '12:00', '14:00'),
        ('Вечерняя группа', '18:00', '20:00')
    ]
    cursor.executemany("""
                       INSERT
                           OR IGNORE
                       INTO schedules (name, time_start, time_end)
                       VALUES (?, ?, ?)
                       """, schedules)

    # Курсы
    courses = [
        ('🇯🇵 Японский язык', 'Изучение японского языка с нуля', 12, 48, 550000, 1300000, 'beginner'),
        ('🇬🇧 Английский язык', 'Изучение английского языка с нуля', 12, 48, 450000, 1200000, 'beginner')
    ]
    cursor.executemany("""
                       INSERT
                           OR IGNORE
                       INTO courses (name, description, duration_months, lessons_count,
                                     price_group, price_individual, level)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       """, courses)


class Database:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.logger = logging.getLogger(__name__)

        # Инициализируем схему при первом запуске
        self._init_schema()

        # Инициализируем репозитории (ленивая загрузка)
        self._registrations = None
        self._students = None
        self._teachers = None
        self._courses = None
        self._groups = None
        self._admins = None
        self._lessons = None
        self._feedback = None
        self._reminders = None

    def _init_schema(self):
        """Инициализировать схему БД (если не существует)"""
        try:
            with self.get_connection() as conn:
                # Проверяем существование основных таблиц
                cursor = conn.cursor()
                cursor.execute("""
                               SELECT name
                               FROM sqlite_master
                               WHERE type = 'table'
                                 AND name = 'users'
                               """)
                if not cursor.fetchone():
                    # БД пустая, нужно создать схему
                    self.logger.info("Initializing database schema...")
                    self._create_schema(conn)
        except Exception as e:
            self.logger.error(f"Error initializing schema: {e}")

    def _create_schema(self, conn: sqlite3.Connection):
        """Создать схему БД из SQL файла или встроенных команд"""
        # Здесь можно загрузить optimized_schema.sql или создать таблицы программно
        # Для краткости используем минимальный набор таблиц

        cursor = conn.cursor()

        # Пользователи
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS users
                       (
                           id
                               INTEGER
                               PRIMARY
                                   KEY
                               AUTOINCREMENT,
                           telegram_id
                               INTEGER
                               UNIQUE
                               NOT
                                   NULL,
                           username
                               TEXT,
                           full_name
                               TEXT,
                           phone
                               TEXT,
                           email
                               TEXT,
                           created_at
                               TIMESTAMP
                               DEFAULT
                                   CURRENT_TIMESTAMP,
                           updated_at
                               TIMESTAMP
                               DEFAULT
                                   CURRENT_TIMESTAMP,
                           is_active
                               BOOLEAN
                               DEFAULT
                                   1
                       )
                       """)

        # Администраторы
        cursor.execute("""
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
                                   1,
                           FOREIGN
                               KEY
                               (
                                user_id
                                   ) REFERENCES users
                               (
                                id
                                   )
                       )
                       """)

        # Курсы
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS courses
                       (
                           id
                               INTEGER
                               PRIMARY
                                   KEY
                               AUTOINCREMENT,
                           name
                               TEXT
                               UNIQUE
                               NOT
                                   NULL,
                           description
                               TEXT,
                           duration_months
                               INTEGER,
                           lessons_count
                               INTEGER,
                           price_group
                               INTEGER,
                           price_individual
                               INTEGER,
                           level
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

        # Типы обучения
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS training_types
                       (
                           id
                               INTEGER
                               PRIMARY
                                   KEY
                               AUTOINCREMENT,
                           name
                               TEXT
                               UNIQUE
                               NOT
                                   NULL,
                           description
                               TEXT,
                           is_active
                               BOOLEAN
                               DEFAULT
                                   1,
                           created_at
                               TIMESTAMP
                               DEFAULT
                                   CURRENT_TIMESTAMP
                       )
                       """)

        # Расписания
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS schedules
                       (
                           id
                               INTEGER
                               PRIMARY
                                   KEY
                               AUTOINCREMENT,
                           name
                               TEXT
                               UNIQUE
                               NOT
                                   NULL,
                           time_start
                               TEXT,
                           time_end
                               TEXT,
                           is_active
                               BOOLEAN
                               DEFAULT
                                   1,
                           created_at
                               TIMESTAMP
                               DEFAULT
                                   CURRENT_TIMESTAMP
                       )
                       """)

        # Статусы студентов
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS student_statuses
                       (
                           id
                               INTEGER
                               PRIMARY
                                   KEY
                               AUTOINCREMENT,
                           code
                               TEXT
                               UNIQUE
                               NOT
                                   NULL,
                           name
                               TEXT
                               NOT
                                   NULL,
                           description
                               TEXT,
                           created_at
                               TIMESTAMP
                               DEFAULT
                                   CURRENT_TIMESTAMP
                       )
                       """)

        # Регистрации (ЕДИНАЯ ТАБЛИЦА!)
        cursor.execute("""
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
                           course_id
                               INTEGER
                               NOT
                                   NULL,
                           training_type_id
                               INTEGER,
                           schedule_id
                               INTEGER,
                           status_code
                               TEXT
                               DEFAULT
                                   'active',
                           created_at
                               TIMESTAMP
                               DEFAULT
                                   CURRENT_TIMESTAMP,
                           consultation_time
                               TIMESTAMP
                               NULL,
                           trial_lesson_time
                               TIMESTAMP
                               NULL,
                           enrollment_date
                               TIMESTAMP
                               NULL,
                           notified
                               BOOLEAN
                               DEFAULT
                                   0,
                           reminder_sent
                               BOOLEAN
                               DEFAULT
                                   0,
                           source
                               TEXT,
                           notes
                               TEXT,
                           updated_at
                               TIMESTAMP
                               DEFAULT
                                   CURRENT_TIMESTAMP,
                           FOREIGN
                               KEY
                               (
                                user_id
                                   ) REFERENCES users
                               (
                                id
                                   ),
                           FOREIGN KEY
                               (
                                course_id
                                   ) REFERENCES courses
                               (
                                id
                                   ),
                           FOREIGN KEY
                               (
                                training_type_id
                                   ) REFERENCES training_types
                               (
                                id
                                   ),
                           FOREIGN KEY
                               (
                                schedule_id
                                   ) REFERENCES schedules
                               (
                                id
                                   ),
                           FOREIGN KEY
                               (
                                status_code
                                   ) REFERENCES student_statuses
                               (
                                code
                                   )
                       )
                       """)

        # Студенты
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS students
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
                           student_code
                               TEXT
                               UNIQUE,
                           enrollment_date
                               DATE
                               DEFAULT
                                   CURRENT_DATE,
                           graduation_date
                               DATE,
                           notes
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
                                user_id
                                   ) REFERENCES users
                               (
                                id
                                   )
                       )
                       """)

        # Преподаватели
        cursor.execute("""
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
                           bio
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

        # Группы
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS groups
                       (
                           id
                               INTEGER
                               PRIMARY
                                   KEY
                               AUTOINCREMENT,
                           name
                               TEXT
                               UNIQUE
                               NOT
                                   NULL,
                           course_id
                               INTEGER
                               NOT
                                   NULL,
                           teacher_id
                               INTEGER,
                           schedule_id
                               INTEGER,
                           max_students
                               INTEGER
                               DEFAULT
                                   10,
                           current_students
                               INTEGER
                               DEFAULT
                                   0,
                           start_date
                               DATE,
                           end_date
                               DATE,
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
                                   ),
                           FOREIGN KEY
                               (
                                schedule_id
                                   ) REFERENCES schedules
                               (
                                id
                                   )
                       )
                       """)

        # Связь студент-группа (many-to-many)
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS student_groups
                       (
                           id
                               INTEGER
                               PRIMARY
                                   KEY
                               AUTOINCREMENT,
                           student_id
                               INTEGER
                               NOT
                                   NULL,
                           group_id
                               INTEGER
                               NOT
                                   NULL,
                           registration_id
                               INTEGER,
                           enrolled_at
                               TIMESTAMP
                               DEFAULT
                                   CURRENT_TIMESTAMP,
                           completed_at
                               TIMESTAMP
                               NULL,
                           status
                               TEXT
                               DEFAULT
                                   'active',
                           FOREIGN
                               KEY
                               (
                                student_id
                                   ) REFERENCES students
                               (
                                id
                                   ),
                           FOREIGN KEY
                               (
                                group_id
                                   ) REFERENCES groups
                               (
                                id
                                   ),
                           FOREIGN KEY
                               (
                                registration_id
                                   ) REFERENCES registrations
                               (
                                id
                                   ),
                           UNIQUE
                               (
                                student_id,
                                group_id
                                   )
                       )
                       """)

        # Уроки
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS lessons
                       (
                           id
                               INTEGER
                               PRIMARY
                                   KEY
                               AUTOINCREMENT,
                           group_id
                               INTEGER
                               NOT
                                   NULL,
                           teacher_id
                               INTEGER
                               NOT
                                   NULL,
                           topic
                               TEXT
                               NOT
                                   NULL,
                           description
                               TEXT,
                           lesson_date
                               DATE
                               NOT
                                   NULL,
                           lesson_time
                               TEXT,
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

        # Посещаемость
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS attendance
                       (
                           id
                               INTEGER
                               PRIMARY
                                   KEY
                               AUTOINCREMENT,
                           lesson_id
                               INTEGER
                               NOT
                                   NULL,
                           student_id
                               INTEGER
                               NOT
                                   NULL,
                           status
                               TEXT
                               DEFAULT
                                   'present',
                           notes
                               TEXT,
                           created_at
                               TIMESTAMP
                               DEFAULT
                                   CURRENT_TIMESTAMP,
                           FOREIGN
                               KEY
                               (
                                lesson_id
                                   ) REFERENCES lessons
                               (
                                id
                                   ),
                           FOREIGN KEY
                               (
                                student_id
                                   ) REFERENCES students
                               (
                                id
                                   ),
                           UNIQUE
                               (
                                lesson_id,
                                student_id
                                   )
                       )
                       """)

        # Напоминания
        cursor.execute("""
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
                                   0,
                           created_at
                               TIMESTAMP
                               DEFAULT
                                   CURRENT_TIMESTAMP,
                           FOREIGN
                               KEY
                               (
                                user_id
                                   ) REFERENCES users
                               (
                                id
                                   )
                       )
                       """)

        # Отзывы
        cursor.execute("""
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
                           registration_id
                                      INTEGER,
                           course_id
                                      INTEGER,
                           teacher_id
                                      INTEGER,
                           rating
                                      INTEGER
                               CHECK
                                   (
                                   rating
                                       >=
                                   1
                                       AND
                                   rating
                                       <=
                                   5
                                   ),
                           comment    TEXT,
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY
                               (
                                user_id
                                   ) REFERENCES users
                               (
                                id
                                   ),
                           FOREIGN KEY
                               (
                                registration_id
                                   ) REFERENCES registrations
                               (
                                id
                                   ),
                           FOREIGN KEY
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

        # Создаем индексы
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_registrations_user ON registrations(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_registrations_status ON registrations(status_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_user ON students(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_groups_student ON student_groups(student_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_groups_group ON student_groups(group_id)")

        # Инициализируем справочные данные
        _init_reference_data(cursor)

        conn.commit()
        self.logger.info("database schema created successfully")

    @contextmanager
    def get_connection(self):
        """
        Context manager для безопасной работы с подключением

        Yields:
            sqlite3.Connection: Подключение к БД

        Example:
            >>> with db.get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT * FROM users")
        """
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # Доступ к полям по имени
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"database error: {e}")
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Выполнить SELECT запрос

        Args:
            query: SQL запрос
            params: Параметры запроса

        Returns:
            List[Dict]: Список результатов
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Выполнить INSERT/UPDATE/DELETE

        Args:
            query: SQL запрос
            params: Параметры запроса

        Returns:
            int: Количество затронутых строк
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount

    def execute_insert(self, query: str, params: tuple = ()) -> int:
        """
        Выполнить INSERT и вернуть ID новой записи

        Args:
            query: SQL запрос
            params: Параметры запроса

        Returns:
            int: ID новой записи
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid

    # ============================================
    # ЛЕНИВАЯ ЗАГРУЗКА РЕПОЗИТОРИЕВ
    # ============================================

    @property
    def registrations(self):
        """Репозиторий регистраций"""
        if self._registrations is None:
            from .registrations import RegistrationRepository
            self._registrations = RegistrationRepository(self)
        return self._registrations

    @property
    def students(self):
        """Репозиторий студентов"""
        if self._students is None:
            from .students import StudentRepository
            self._students = StudentRepository(self)
        return self._students

    @property
    def teachers(self):
        """Репозиторий преподавателей"""
        if self._teachers is None:
            from .teachers import TeacherRepository
            self._teachers = TeacherRepository(self)
        return self._teachers

    @property
    def courses(self):
        """Репозиторий курсов"""
        if self._courses is None:
            from .courses import CourseRepository
            self._courses = CourseRepository(self)
        return self._courses

    @property
    def groups(self):
        """Репозиторий групп"""
        if self._groups is None:
            from .groups import GroupRepository
            self._groups = GroupRepository(self)
        return self._groups

    @property
    def admins(self):
        """Репозиторий администраторов"""
        if self._admins is None:
            from .admins import AdminRepository
            self._admins = AdminRepository(self)
        return self._admins

    @property
    def lessons(self):
        """Репозиторий уроков"""
        if self._lessons is None:
            from .lessons import LessonRepository
            self._lessons = LessonRepository(self)
        return self._lessons

    @property
    def feedback_repo(self):
        """Репозиторий отзывов"""
        if self._feedback is None:
            from .feedback import FeedbackRepository
            self._feedback = FeedbackRepository(self)
        return self._feedback

    @property
    def reminders_repo(self):
        """Репозиторий напоминаний"""
        if self._reminders is None:
            from .reminders import ReminderRepository
            self._reminders = ReminderRepository(self)
        return self._reminders

    # ============================================
    # МЕТОДЫ СОВМЕСТИМОСТИ (для старого кода)
    # ============================================

    def get_all_admins(self):
        """Получить всех администраторов (совместимость)"""
        return self.admins.get_all()

    def check_database_structure(self):
        """Проверить структуру БД (совместимость)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                self.logger.info(f"database tables: {', '.join(tables)}")
                return True
        except Exception as e:
            self.logger.error(f"Error checking database structure: {e}")
            return False

