import sqlite3
import logging
from config import Config

logger = logging.getLogger(__name__)
config = Config()


def initialize_database():
    """Инициализация и обновление структуры базы данных"""
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()

        # Проверяем существование таблицы feedback
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='feedback'
        """)

        if not cursor.fetchone():
            logger.info("Creating feedback table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    full_name TEXT,
                    feedback_type TEXT NOT NULL,
                    rating INTEGER,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'new'
                )
            """)
            logger.info("✅ Feedback table created")

        # Проверяем существование таблицы admins
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='admins'
        """)

        if not cursor.fetchone():
            logger.info("Creating admins table...")
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

            # Добавляем администраторов из конфига
            for admin_id in config.ADMIN_IDS:
                cursor.execute("""
                    INSERT OR IGNORE INTO admins (user_id, is_active)
                    VALUES (?, 1)
                """, (admin_id,))

            logger.info("✅ Admins table created and populated")

        # Проверяем существование таблицы teachers
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='teachers'
        """)

        if not cursor.fetchone():
            logger.info("Creating teachers table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS teachers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    specialization TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ Teachers table created")

        # Проверяем существование таблицы courses
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='courses'
        """)

        if not cursor.fetchone():
            logger.info("Creating courses table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    duration_months INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ Courses table created")

        # Проверяем существование таблицы groups
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='groups'
        """)

        if not cursor.fetchone():
            logger.info("Creating groups table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    course_id INTEGER,
                    teacher_id INTEGER,
                    start_date DATE,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES courses(id),
                    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
                )
            """)
            logger.info("✅ Groups table created")

        # Проверяем существование таблицы lessons
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='lessons'
        """)

        if not cursor.fetchone():
            logger.info("Creating lessons table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    teacher_id INTEGER NOT NULL,
                    topic TEXT NOT NULL,
                    lesson_date TIMESTAMP NOT NULL,
                    duration_minutes INTEGER DEFAULT 60,
                    is_completed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES groups(id),
                    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
                )
            """)
            logger.info("✅ Lessons table created")

        # Проверяем существование таблицы registrations
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='registrations'
        """)

        if not cursor.fetchone():
            logger.info("Creating registrations table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    course TEXT NOT NULL,
                    training_type TEXT NOT NULL,
                    schedule TEXT NOT NULL,
                    price TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    progress TEXT,
                    trial_lesson_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("✅ Registrations table created")
        else:
            # Таблица существует, проверяем и добавляем недостающие колонки
            cursor.execute("PRAGMA table_info(registrations)")
            columns = [column[1] for column in cursor.fetchall()]

            if 'progress' not in columns:
                logger.info("Adding 'progress' column...")
                cursor.execute("ALTER TABLE registrations ADD COLUMN progress TEXT")
                logger.info("✅ Added 'progress' column to registrations")

            if 'trial_lesson_time' not in columns:
                logger.info("Adding 'trial_lesson_time' column...")
                cursor.execute("ALTER TABLE registrations ADD COLUMN trial_lesson_time TIMESTAMP")
                logger.info("✅ Added 'trial_lesson_time' column to registrations")

            if 'updated_at' not in columns:
                logger.info("Adding 'updated_at' column...")
                # SQLite не позволяет DEFAULT CURRENT_TIMESTAMP в ALTER TABLE
                # Добавляем колонку без DEFAULT, затем обновляем существующие записи
                cursor.execute("ALTER TABLE registrations ADD COLUMN updated_at TIMESTAMP")
                cursor.execute("UPDATE registrations SET updated_at = created_at WHERE updated_at IS NULL")
                logger.info("✅ Added 'updated_at' column to registrations")

        conn.commit()
        conn.close()

        logger.info("✅ Database initialization completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}", exc_info=True)
        return False


def check_database_integrity():
    """Проверка целостности базы данных"""
    try:
        conn = sqlite3.connect(config.DB_NAME)
        cursor = conn.cursor()

        # Получаем список всех таблиц
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
        """)
        tables = [row[0] for row in cursor.fetchall()]

        logger.info(f"📋 Existing tables: {', '.join(tables)}")

        required_tables = [
            'registrations', 'feedback', 'admins',
            'teachers', 'courses', 'groups', 'lessons'
        ]

        missing_tables = [t for t in required_tables if t not in tables]

        if missing_tables:
            logger.warning(f"⚠️ Missing tables: {', '.join(missing_tables)}")
            return False

        # Проверяем колонки в registrations
        cursor.execute("PRAGMA table_info(registrations)")
        reg_columns = [column[1] for column in cursor.fetchall()]

        required_columns = [
            'id', 'user_id', 'name', 'phone', 'course',
            'training_type', 'schedule', 'price', 'status',
            'progress', 'trial_lesson_time', 'created_at', 'updated_at'
        ]

        missing_columns = [c for c in required_columns if c not in reg_columns]

        if missing_columns:
            logger.warning(f"⚠️ Missing columns in registrations: {', '.join(missing_columns)}")
            return False

        logger.info("✅ All required tables and columns exist")
        conn.close()
        return True

    except Exception as e:
        logger.error(f"❌ Database check error: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("🔧 Starting database initialization...")
    if initialize_database():
        print("✅ Database initialized successfully")
        if check_database_integrity():
            print("✅ Database integrity check passed")
        else:
            print("⚠️ Database integrity check found issues")
    else:
        print("❌ Database initialization failed")