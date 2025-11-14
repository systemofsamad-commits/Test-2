import os
import sqlite3
from datetime import datetime

DB_NAME = "education_center.db"


def recreate_database():
    """Пересоздать базу данных с нуля"""

    # Удаляем старую БД если есть
    if os.path.exists(DB_NAME):
        backup_name = f"{DB_NAME}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"📦 Создаю backup: {backup_name}")
        try:
            os.rename(DB_NAME, backup_name)
        except Exception:
            os.remove(DB_NAME)
        print(f"❌ Старая БД удалена (backup не удался)")

    print(f"🔨 Создаю новую БД: {DB_NAME}")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    create_minimal_schema(cursor)

    conn.commit()
    conn.close()

    print(f"✅ База данных {DB_NAME} успешно создана!")
    print("\n🎯 Теперь можешь запускать бота: python main.py")


def create_minimal_schema(cursor):
    """Создать минимальную схему"""

    print("📝 Создаю таблицы...")

    # Пользователи
    cursor.execute("""
                   CREATE TABLE users
                   (
                       id          INTEGER PRIMARY KEY AUTOINCREMENT,
                       telegram_id INTEGER UNIQUE NOT NULL,
                       username    TEXT,
                       full_name   TEXT,
                       phone       TEXT,
                       email       TEXT,
                       created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       is_active   BOOLEAN   DEFAULT 1
                   )
                   """)

    # Администраторы
    cursor.execute("""
                   CREATE TABLE admins
                   (
                       id         INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id    INTEGER UNIQUE NOT NULL,
                       username   TEXT,
                       full_name  TEXT,
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       is_active  BOOLEAN   DEFAULT 1
                   )
                   """)

    # Добавляем админа
    cursor.execute("INSERT INTO admins (user_id, is_active) VALUES (866916345, 1)")

    # Курсы
    cursor.execute("""
                   CREATE TABLE courses
                   (
                       id               INTEGER PRIMARY KEY AUTOINCREMENT,
                       name             TEXT UNIQUE NOT NULL,
                       description      TEXT,
                       duration_months  INTEGER,
                       lessons_count    INTEGER,
                       price_group      INTEGER,
                       price_individual INTEGER,
                       level            TEXT,
                       created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       is_active        BOOLEAN   DEFAULT 1
                   )
                   """)

    # Типы обучения
    cursor.execute("""
                   CREATE TABLE training_types
                   (
                       id          INTEGER PRIMARY KEY AUTOINCREMENT,
                       name        TEXT UNIQUE NOT NULL,
                       description TEXT,
                       is_active   BOOLEAN   DEFAULT 1,
                       created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   """)

    # Расписания
    cursor.execute("""
                   CREATE TABLE schedules
                   (
                       id         INTEGER PRIMARY KEY AUTOINCREMENT,
                       name       TEXT UNIQUE NOT NULL,
                       time_start TEXT,
                       time_end   TEXT,
                       is_active  BOOLEAN   DEFAULT 1,
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   """)

    # Статусы
    cursor.execute("""
                   CREATE TABLE student_statuses
                   (
                       id          INTEGER PRIMARY KEY AUTOINCREMENT,
                       code        TEXT UNIQUE NOT NULL,
                       name        TEXT        NOT NULL,
                       description TEXT,
                       created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   """)

    # Регистрации
    cursor.execute("""
                   CREATE TABLE registrations
                   (
                       id                INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id           INTEGER NOT NULL,
                       course_id         INTEGER NOT NULL,
                       training_type_id  INTEGER,
                       schedule_id       INTEGER,
                       status_code       TEXT      DEFAULT 'active',
                       created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       consultation_time TIMESTAMP NULL,
                       trial_lesson_time TIMESTAMP NULL,
                       enrollment_date   TIMESTAMP NULL,
                       notified          BOOLEAN   DEFAULT 0,
                       reminder_sent     BOOLEAN   DEFAULT 0,
                       source            TEXT,
                       notes             TEXT,
                       updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   """)

    # Студенты
    cursor.execute("""
                   CREATE TABLE students
                   (
                       id              INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id         INTEGER UNIQUE NOT NULL,
                       student_code    TEXT UNIQUE,
                       enrollment_date DATE      DEFAULT CURRENT_DATE,
                       graduation_date DATE,
                       notes           TEXT,
                       created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       is_active       BOOLEAN   DEFAULT 1
                   )
                   """)

    # Преподаватели
    cursor.execute("""
                   CREATE TABLE teachers
                   (
                       id             INTEGER PRIMARY KEY AUTOINCREMENT,
                       name           TEXT NOT NULL,
                       phone          TEXT NOT NULL,
                       email          TEXT,
                       specialization TEXT,
                       experience     TEXT,
                       bio            TEXT,
                       created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       is_active      BOOLEAN   DEFAULT 1
                   )
                   """)

    # Группы
    cursor.execute("""
                   CREATE TABLE groups
                   (
                       id               INTEGER PRIMARY KEY AUTOINCREMENT,
                       name             TEXT UNIQUE NOT NULL,
                       course_id        INTEGER     NOT NULL,
                       teacher_id       INTEGER,
                       schedule_id      INTEGER,
                       max_students     INTEGER   DEFAULT 10,
                       current_students INTEGER   DEFAULT 0,
                       start_date       DATE,
                       end_date         DATE,
                       created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       is_active        BOOLEAN   DEFAULT 1
                   )
                   """)

    # Уроки
    cursor.execute("""
                   CREATE TABLE lessons
                   (
                       id               INTEGER PRIMARY KEY AUTOINCREMENT,
                       group_id         INTEGER NOT NULL,
                       teacher_id       INTEGER NOT NULL,
                       topic            TEXT    NOT NULL,
                       description      TEXT,
                       lesson_date      DATE    NOT NULL,
                       lesson_time      TEXT,
                       duration_minutes INTEGER   DEFAULT 60,
                       materials        TEXT,
                       homework         TEXT,
                       created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   """)

    # Напоминания
    cursor.execute("""
                   CREATE TABLE reminders
                   (
                       id         INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id    INTEGER   NOT NULL,
                       text       TEXT      NOT NULL,
                       due_date   TIMESTAMP NOT NULL,
                       sent       BOOLEAN   DEFAULT 0,
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   """)

    # Отзывы
    cursor.execute("""
                   CREATE TABLE feedback
                   (
                       id              INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id         INTEGER NOT NULL,
                       registration_id INTEGER,
                       course_id       INTEGER,
                       teacher_id      INTEGER,
                       rating          INTEGER CHECK (rating >= 1 AND rating <= 5),
                       comment         TEXT,
                       created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                   )
                   """)

    print("✅ Таблицы созданы")
    print("📝 Создаю индексы...")

    # Индексы
    cursor.execute("CREATE INDEX idx_users_telegram_id ON users(telegram_id)")
    cursor.execute("CREATE INDEX idx_registrations_user ON registrations(user_id)")
    cursor.execute("CREATE INDEX idx_registrations_status ON registrations(status_code)")

    print("✅ Индексы созданы")
    print("📝 Заполняю справочники...")

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 ПЕРЕСОЗДАНИЕ БАЗЫ ДАННЫХ")
    print("=" * 60)
    print()

    recreate_database()
