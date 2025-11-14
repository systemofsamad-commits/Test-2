"""
Скрипт для полной очистки и пересоздания БД
Запусти ПЕРЕД запуском бота!
"""
import os
import sqlite3
from datetime import datetime

# Имена файлов
DB_NAME = "education_center.db"
SQL_FILE = "optimized_schema.sql"

print("=" * 60)
print("🔧 ОЧИСТКА И ПЕРЕСОЗДАНИЕ БАЗЫ ДАННЫХ")
print("=" * 60)
print()

# ШАГ 1: Удаляем старые файлы
print("📦 Шаг 1: Удаление старых файлов...")

if os.path.exists(DB_NAME):
    backup_name = f"{DB_NAME}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        os.rename(DB_NAME, backup_name)
        print(f"   ✅ БД сохранена в: {backup_name}")
    except:
        os.remove(DB_NAME)
        print(f"   ✅ Старая БД удалена")

if os.path.exists(SQL_FILE):
    try:
        os.remove(SQL_FILE)
        print(f"   ✅ {SQL_FILE} удален (он мешал)")
    except Exception as e:
        print(f"   ⚠️  Не удалось удалить {SQL_FILE}: {e}")

print()

# ШАГ 2: Создаем новую БД
print("🔨 Шаг 2: Создание новой БД...")

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Таблицы
print("   📝 Создаю таблицы...")

# users
cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        full_name TEXT,
        phone TEXT,
        email TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
""")

# admins
cursor.execute("""
    CREATE TABLE admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        full_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
""")

# Добавляем админа
cursor.execute("INSERT INTO admins (user_id, is_active) VALUES (866916345, 1)")

# courses
cursor.execute("""
    CREATE TABLE courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        duration_months INTEGER,
        lessons_count INTEGER,
        price_group INTEGER,
        price_individual INTEGER,
        level TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
""")

# training_types
cursor.execute("""
    CREATE TABLE training_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# schedules
cursor.execute("""
    CREATE TABLE schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        time_start TEXT,
        time_end TEXT,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# student_statuses
cursor.execute("""
    CREATE TABLE student_statuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# registrations
cursor.execute("""
    CREATE TABLE registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        training_type_id INTEGER,
        schedule_id INTEGER,
        status_code TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        consultation_time TIMESTAMP NULL,
        trial_lesson_time TIMESTAMP NULL,
        enrollment_date TIMESTAMP NULL,
        notified BOOLEAN DEFAULT 0,
        reminder_sent BOOLEAN DEFAULT 0,
        source TEXT,
        notes TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# students
cursor.execute("""
    CREATE TABLE students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        student_code TEXT UNIQUE,
        enrollment_date DATE DEFAULT CURRENT_DATE,
        graduation_date DATE,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
""")

# teachers
cursor.execute("""
    CREATE TABLE teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        specialization TEXT,
        experience TEXT,
        bio TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
""")

# groups
cursor.execute("""
    CREATE TABLE groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        course_id INTEGER NOT NULL,
        teacher_id INTEGER,
        schedule_id INTEGER,
        max_students INTEGER DEFAULT 10,
        current_students INTEGER DEFAULT 0,
        start_date DATE,
        end_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
""")

# student_groups
cursor.execute("""
    CREATE TABLE student_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        group_id INTEGER NOT NULL,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
""")

# lessons
cursor.execute("""
    CREATE TABLE lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        topic TEXT NOT NULL,
        description TEXT,
        lesson_date DATE NOT NULL,
        lesson_time TEXT,
        duration_minutes INTEGER DEFAULT 60,
        materials TEXT,
        homework TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# attendance
cursor.execute("""
    CREATE TABLE attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        status TEXT DEFAULT 'present',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# reminders
cursor.execute("""
    CREATE TABLE reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        due_date TIMESTAMP NOT NULL,
        sent BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# feedback
cursor.execute("""
    CREATE TABLE feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        registration_id INTEGER,
        course_id INTEGER,
        teacher_id INTEGER,
        rating INTEGER CHECK(rating >= 1 AND rating <= 5),
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

print("   ✅ Таблицы созданы")
print()

# ШАГ 3: Индексы
print("📝 Шаг 3: Создание индексов...")

cursor.execute("CREATE INDEX idx_users_telegram_id ON users(telegram_id)")
cursor.execute("CREATE INDEX idx_registrations_user ON registrations(user_id)")
cursor.execute("CREATE INDEX idx_registrations_status ON registrations(status_code)")
cursor.execute("CREATE INDEX idx_lessons_group ON lessons(group_id)")
cursor.execute("CREATE INDEX idx_student_groups_student ON student_groups(student_id)")
cursor.execute("CREATE INDEX idx_student_groups_group ON student_groups(group_id)")

print("   ✅ Индексы созданы")
print()

# ШАГ 4: Заполнение справочников
print("📊 Шаг 4: Заполнение справочников...")

# Статусы
statuses = [
    ('active', 'Активные', 'Активно'),
    ('trial', 'Пробный урок', 'Пробный'),
    ('studying', 'Обучаются', 'Учатся'),
    ('frozen', 'Заморожены', 'Заморожены'),
    ('waiting_payment', 'Ожидание оплаты', 'Ждут'),
    ('completed', 'Завершили', 'Завершили')
]
cursor.executemany(
    "INSERT INTO student_statuses (code, name, description) VALUES (?, ?, ?)",
    statuses
)

# Типы обучения
training_types = [
    ('Групповые занятия (80 минут)', 'Группа'),
    ('Индивидуальное обучение (1 час)', 'Индивидуально'),
    ('Групповые занятия (60 минут)', 'Группа')
]
cursor.executemany(
    "INSERT INTO training_types (name, description) VALUES (?, ?)",
    training_types
)

# Расписания
schedules = [
    ('Утренняя группа', '09:00', '11:00'),
    ('Обеденная группа', '12:00', '14:00'),
    ('Вечерняя группа', '18:00', '20:00')
]
cursor.executemany(
    "INSERT INTO schedules (name, time_start, time_end) VALUES (?, ?, ?)",
    schedules
)

# Курсы
courses = [
    ('🇯🇵 Японский язык', 'Японский', 12, 48, 550000, 1300000, 'beginner'),
    ('🇬🇧 Английский язык', 'Английский', 12, 48, 450000, 1200000, 'beginner'),
    ('🇰🇷 Корейский язык', 'Корейский', 12, 48, 550000, 1300000, 'beginner'),
]
cursor.executemany(
    "INSERT INTO courses (name, description, duration_months, lessons_count, price_group, price_individual, level) VALUES (?, ?, ?, ?, ?, ?, ?)",
    courses
)

print("   ✅ Справочники заполнены")
print()

# Commit и закрытие
conn.commit()
conn.close()

print("=" * 60)
print("✅ БАЗА ДАННЫХ УСПЕШНО СОЗДАНА!")
print("=" * 60)
print()
print(f"📁 Файл: {DB_NAME}")
print(f"📊 Таблиц: 16")
print(f"👤 Админов: 1 (ID: 866916345)")
print(f"📚 Курсов: 3")
print()
print("🎯 Теперь можешь запускать бота:")
print("   python main.py")
print()