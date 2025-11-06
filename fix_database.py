import sqlite3
import logging
import sys
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_path():
    """Получить путь к базе данных"""
    try:
        from config import Config
        config = Config()
        return config.DB_NAME
    except:
        return "bot_database.db"


def add_missing_columns(cursor):
    """Добавление недостающих колонок в существующие таблицы"""
    try:
        # Проверяем колонки в registrations
        cursor.execute("PRAGMA table_info(registrations)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'progress' not in columns:
            logger.info("Adding 'progress' column...")
            cursor.execute("ALTER TABLE registrations ADD COLUMN progress TEXT")
            logger.info("✅ Added 'progress' column")

        if 'trial_lesson_time' not in columns:
            logger.info("Adding 'trial_lesson_time' column...")
            cursor.execute("ALTER TABLE registrations ADD COLUMN trial_lesson_time TIMESTAMP")
            logger.info("✅ Added 'trial_lesson_time' column")

        if 'updated_at' not in columns:
            logger.info("Adding 'updated_at' column...")
            # Добавляем без DEFAULT, затем обновляем
            cursor.execute("ALTER TABLE registrations ADD COLUMN updated_at TIMESTAMP")
            cursor.execute("UPDATE registrations SET updated_at = created_at WHERE updated_at IS NULL")
            logger.info("✅ Added 'updated_at' column")

        return True
    except Exception as e:
        logger.error(f"❌ Error adding columns: {e}")
        return False


def create_all_tables(cursor):
    """Создание всех необходимых таблиц"""

    tables = {
        'registrations': """
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
        """,

        'feedback': """
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
        """,

        'admins': """
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """,

        'teachers': """
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                specialization TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,

        'courses': """
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                duration_months INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,

        'groups': """
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
        """,

        'lessons': """
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
        """
    }

    for table_name, create_sql in tables.items():
        try:
            cursor.execute(create_sql)
            logger.info(f"✅ Table '{table_name}' created/verified")
        except Exception as e:
            logger.error(f"❌ Error creating table '{table_name}': {e}")
            return False

    return True


def check_and_fix_database():
    """Проверка и исправление базы данных"""

    db_path = get_db_path()
    logger.info(f"📂 Database path: {db_path}")

    try:
        # Подключение к БД
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        logger.info("✅ Connected to database")

        # Создание всех таблиц
        if not create_all_tables(cursor):
            logger.error("❌ Failed to create tables")
            return False

        # Проверка существующих таблиц
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
            ORDER BY name
        """)

        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"📋 Existing tables: {', '.join(tables)}")

        # Добавление администраторов из конфига
        try:
            from config import Config
            config = Config()

            for admin_id in config.ADMIN_IDS:
                cursor.execute("""
                    INSERT OR IGNORE INTO admins (user_id, is_active)
                    VALUES (?, 1)
                """, (admin_id,))
                logger.info(f"✅ Admin {admin_id} added/verified")
        except Exception as e:
            logger.warning(f"⚠️ Could not add admins: {e}")

        # Сохранение изменений
        conn.commit()
        conn.close()

        logger.info("✅ Database check and fix completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Database error: {e}", exc_info=True)
        return False


def main():
    """Главная функция"""
    print("=" * 60)
    print("🔧 DATABASE FIX SCRIPT")
    print("=" * 60)
    print()

    if check_and_fix_database():
        print()
        print("=" * 60)
        print("✅ DATABASE SUCCESSFULLY FIXED!")
        print("=" * 60)
        print()
        print("You can now start your bot with: python main.py")
        return 0
    else:
        print()
        print("=" * 60)
        print("❌ DATABASE FIX FAILED!")
        print("=" * 60)
        print()
        print("Please check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())