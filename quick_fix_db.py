import sqlite3
import sys

def get_db_name():
    try:
        from config import Config
        return Config().DB_NAME
    except:
        return "bot_database.db"

def main():
    db_name = get_db_name()
    print(f"🔧 Fixing database: {db_name}")

    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # 1. Создаём таблицу feedback если не существует
        print("📝 Creating feedback table...")
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
        print("✅ Feedback table OK")

        # 2. Создаём таблицу admins если не существует
        print("📝 Creating admins table...")
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
        print("✅ Admins table OK")

        # 3. Создаём остальные таблицы
        print("📝 Creating other tables...")

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

        print("✅ All tables created")

        # 4. Проверяем и добавляем колонки в registrations
        print("📝 Checking registrations table...")
        cursor.execute("PRAGMA table_info(registrations)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'progress' not in columns:
            print("  Adding 'progress' column...")
            cursor.execute("ALTER TABLE registrations ADD COLUMN progress TEXT")
            print("  ✅ Added")

        if 'trial_lesson_time' not in columns:
            print("  Adding 'trial_lesson_time' column...")
            cursor.execute("ALTER TABLE registrations ADD COLUMN trial_lesson_time TIMESTAMP")
            print("  ✅ Added")

        if 'updated_at' not in columns:
            print("  Adding 'updated_at' column...")
            cursor.execute("ALTER TABLE registrations ADD COLUMN updated_at TIMESTAMP")
            cursor.execute("UPDATE registrations SET updated_at = created_at WHERE updated_at IS NULL")
            print("  ✅ Added")

        # 5. Добавляем админов из конфига
        try:
            from config import Config
            config = Config()
            print(f"📝 Adding admins from config...")
            for admin_id in config.ADMIN_IDS:
                cursor.execute("""
                    INSERT OR IGNORE INTO admins (user_id, is_active)
                    VALUES (?, 1)
                """, (admin_id,))
                print(f"  ✅ Admin {admin_id} added")
        except Exception as e:
            print(f"  ⚠️ Could not add admins: {e}")

        # Сохраняем изменения
        conn.commit()

        # Показываем список таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]

        print("\n📋 Database tables:")
        for table in tables:
            print(f"  • {table}")

        conn.close()

        print("\n" + "="*50)
        print("✅ DATABASE FIXED SUCCESSFULLY!")
        print("="*50)
        print("\nYou can now run: python main.py")
        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())