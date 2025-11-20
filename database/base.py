"""
Base database Class - ИСПРАВЛЕНО ДЛЯ PYTHON 3.8+
Базовый класс для работы с SQLite

✅ ИСПРАВЛЕНО: Добавлен импорт Optional, Tuple из typing
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple  # ✅ ДОБАВЛЕНО Optional, Tuple

logger = logging.getLogger(__name__)


def _init_reference_data(cursor: sqlite3.Cursor) -> None:
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
        INSERT OR IGNORE INTO student_statuses (code, name, description)
        VALUES (?, ?, ?)
    """, statuses)

    # Типы обучения
    training_types = [
        ('Групповые занятия (80 минут)', 'Занятия в группе до 10 человек'),
        ('Индивидуальное обучение (1 час)', 'Индивидуальные занятия'),
        ('Групповые занятия (60 минут)', 'Занятия в группе до 15 человек')
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO training_types (name, description)
        VALUES (?, ?)
    """, training_types)

    # Расписания
    schedules = [
        ('Утренняя группа', '09:00', '11:00'),
        ('Обеденная группа', '12:00', '14:00'),
        ('Вечерняя группа', '18:00', '20:00')
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO schedules (name, time_start, time_end)
        VALUES (?, ?, ?)
    """, schedules)

    # Курсы
    courses = [
        ('🇯🇵 Японский язык', 'Изучение японского языка с нуля', 12, 48, 550000, 1300000, 'beginner'),
        ('🇬🇧 Английский язык', 'Изучение английского языка с нуля', 12, 48, 450000, 1200000, 'beginner')
    ]
    cursor.executemany("""
        INSERT OR IGNORE INTO courses (name, description, duration_months, lessons_count,
                                       price_group, price_individual, level)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, courses)


def _create_tables(cursor: sqlite3.Cursor) -> None:
    """Создать все таблицы"""

    # Пользователи
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Курсы
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            duration_months INTEGER,
            lessons_count INTEGER,
            price_group INTEGER,
            price_individual INTEGER,
            level TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)

    # Преподаватели
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            specialization TEXT,
            experience_years INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Статусы студентов (справочник)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_statuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT
        )
    """)

    # Типы обучения (справочник)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    """)

    # Расписания (справочник)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            time_start TEXT,
            time_end TEXT
        )
    """)

    # Регистрации
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            training_type_id INTEGER,
            schedule_id INTEGER,
            status_code TEXT DEFAULT 'trial',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            trial_lesson_time TIMESTAMP,
            consultation_time TIMESTAMP,
            notified BOOLEAN DEFAULT 0,
            reminder_sent BOOLEAN DEFAULT 0,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id),
            FOREIGN KEY (training_type_id) REFERENCES training_types(id),
            FOREIGN KEY (schedule_id) REFERENCES schedules(id),
            FOREIGN KEY (status_code) REFERENCES student_statuses(code)
        )
    """)

    # Студенты
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            registration_id INTEGER,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            student_code TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (registration_id) REFERENCES registrations(id)
        )
    """)

    # Администраторы
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    """)

    # Группы
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            course_id INTEGER NOT NULL,
            teacher_id INTEGER,
            schedule_id INTEGER,
            max_students INTEGER DEFAULT 10,
            current_students INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY (course_id) REFERENCES courses(id),
            FOREIGN KEY (teacher_id) REFERENCES teachers(id),
            FOREIGN KEY (schedule_id) REFERENCES schedules(id)
        )
    """)

    # Студенты в группах
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (group_id) REFERENCES groups(id),
            UNIQUE(student_id, group_id)
        )
    """)

    # Уроки
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            teacher_id INTEGER NOT NULL,
            topic TEXT NOT NULL,
            lesson_date TIMESTAMP NOT NULL,
            duration_minutes INTEGER DEFAULT 60,
            materials TEXT,
            homework TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES groups(id),
            FOREIGN KEY (teacher_id) REFERENCES teachers(id)
        )
    """)

    # Посещаемость
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT DEFAULT 'present',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lesson_id) REFERENCES lessons(id),
            FOREIGN KEY (student_id) REFERENCES students(id),
            UNIQUE(lesson_id, student_id)
        )
    """)

    # Отзывы
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            registration_id INTEGER,
            course_id INTEGER,
            teacher_id INTEGER,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (registration_id) REFERENCES registrations(id),
            FOREIGN KEY (course_id) REFERENCES courses(id),
            FOREIGN KEY (teacher_id) REFERENCES teachers(id)
        )
    """)

    # Напоминания
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            due_date TIMESTAMP NOT NULL,
            sent BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Индексы
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_registrations_user ON registrations(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_registrations_status ON registrations(status_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_user ON students(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_groups_student ON student_groups(student_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_groups_group ON student_groups(group_id)")


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
        self._users = None

    def _init_schema(self) -> None:
        """Инициализировать схему БД (если не существует)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Проверяем существование основных таблиц
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='users'
                """)

                if cursor.fetchone():
                    self.logger.info("Database already initialized")
                    return

                _create_tables(cursor)
                _init_reference_data(cursor)
                conn.commit()
                self.logger.info("Database schema created successfully")

        except Exception as e:
            self.logger.error(f"Error initializing schema: {e}", exc_info=True)
            raise

    @contextmanager
    def get_connection(self):
        """Context manager для безопасной работы с подключением"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Выполнить SELECT запрос"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Выполнить INSERT/UPDATE/DELETE"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount

    def execute_insert(self, query: str, params: tuple = ()) -> Optional[int]:
        """
        ✅ Выполнить INSERT и вернуть ID новой записи

        Returns:
            Optional[int]: ID новой записи или None при ошибке
        """
        try:
            print(f"\n{'=' * 70}")
            print("🔍 EXECUTE_INSERT")
            print(f"{'=' * 70}")
            print(f"📝 Query: {query[:100]}...")
            print(f"📊 Params: {params}")

            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                last_id = cursor.lastrowid

                print(f"✅ lastrowid = {last_id}")

                if last_id == 0:
                    print("⚠️ WARNING: lastrowid = 0!")
                    cursor.execute("SELECT last_insert_rowid()")
                    fetch_result = cursor.fetchone()
                    if fetch_result:
                        actual_rowid = fetch_result[0]
                        print(f"   Actual rowid from DB: {actual_rowid}")
                        if actual_rowid > 0:
                            last_id = actual_rowid

                print(f"{'=' * 70}\n")
                return last_id

        except sqlite3.IntegrityError as e:
            print(f"\n{'=' * 70}")
            print("❌ INTEGRITY ERROR (Foreign Key или Unique constraint)")
            print(f"{'=' * 70}")
            print(f"Ошибка: {e}")
            print(f"{'=' * 70}\n")
            self.logger.error(f"IntegrityError: {e}", exc_info=True)
            return None

        except Exception as e:
            print(f"\n{'=' * 70}")
            print("❌ EXECUTE_INSERT ERROR")
            print(f"{'=' * 70}")
            print(f"Ошибка: {e}")
            print(f"{'=' * 70}\n")
            self.logger.error(f"Error in execute_insert: {e}", exc_info=True)
            return None

    def validate_registration_data(self, user_id: int, course_id: int,
                                   training_type_id: Optional[int] = None,
                                   schedule_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        ✅ Проверить что все ID существуют в БД

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        print(f"\n{'=' * 70}")
        print("🔍 ВАЛИДАЦИЯ ДАННЫХ РЕГИСТРАЦИИ")
        print(f"{'=' * 70}")

        # Проверка user_id
        result = self.execute_query("SELECT id FROM users WHERE id = ?", (user_id,))
        if not result:
            error = f"❌ User ID {user_id} не найден"
            print(error)
            print(f"{'=' * 70}\n")
            return False, error
        print(f"✅ User ID {user_id} найден")

        # Проверка course_id
        result = self.execute_query("SELECT id, name FROM courses WHERE id = ?", (course_id,))
        if not result:
            error = f"❌ Course ID {course_id} не найден"
            print(error)
            print(f"{'=' * 70}\n")
            return False, error
        print(f"✅ Course ID {course_id} найден: {result[0]['name']}")

        # Проверка training_type_id
        if training_type_id:
            result = self.execute_query("SELECT id, name FROM training_types WHERE id = ?", (training_type_id,))
            if not result:
                error = f"❌ Training Type ID {training_type_id} не найден"
                print(error)
                print(f"{'=' * 70}\n")
                return False, error
            print(f"✅ Training Type ID {training_type_id} найден: {result[0]['name']}")

        # Проверка schedule_id
        if schedule_id:
            result = self.execute_query("SELECT id, name FROM schedules WHERE id = ?", (schedule_id,))
            if not result:
                error = f"❌ Schedule ID {schedule_id} не найден"
                print(error)
                print(f"{'=' * 70}\n")
                return False, error
            print(f"✅ Schedule ID {schedule_id} найден: {result[0]['name']}")

        # Проверка статуса
        result = self.execute_query("SELECT code FROM student_statuses WHERE code = 'trial'")
        if not result:
            error = "❌ Статус 'trial' не найден"
            print(error)
            print(f"{'=' * 70}\n")
            return False, error
        print("✅ Статус 'trial' существует")

        print("✅ Все данные валидны!")
        print(f"{'=' * 70}\n")
        return True, "OK"

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

    @property
    def users(self):
        """Репозиторий пользователей"""
        if self._users is None:
            from .user import UserRepository
            self._users = UserRepository(self)
        return self._users

    # ============================================
    # МЕТОДЫ СОВМЕСТИМОСТИ
    # ============================================

    def get_all_admins(self):
        """Получить всех администраторов"""
        return self.admins.get_all()

    def check_database_structure(self) -> bool:
        """Проверить структуру БД"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                self.logger.info(f"Database tables: {', '.join(tables)}")
                return True
        except Exception as e:
            self.logger.error(f"Error checking database: {e}")
            return False

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Получить пользователя по Telegram ID"""
        results = self.execute_query(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        return results[0] if results else None

    def get_registrations_by_user_id(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить регистрации пользователя"""
        return self.execute_query(
            "SELECT * FROM registrations WHERE user_id = ?",
            (user_id,)
        )