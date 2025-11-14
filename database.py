import sqlite3
import os
import shutil
from datetime import datetime
from typing import List, Dict


def get_old_tables(conn: sqlite3.Connection) -> List[str]:
    """Получить список всех таблиц статусов"""
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT name
                   FROM sqlite_master
                   WHERE type = 'table'
                     AND name LIKE 'registrations_%'
                   """)
    return [row[0] for row in cursor.fetchall()]


def _ensure_user_exists(conn: sqlite3.Connection, row_dict: Dict) -> int:
    """Создать или найти пользователя"""
    cursor = conn.cursor()

    # Пытаемся найти по user_id (telegram_id)
    telegram_id = row_dict.get('user_id')
    if telegram_id:
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        result = cursor.fetchone()
        if result:
            return result[0]

    # Создаем нового пользователя
    cursor.execute("""
                   INSERT INTO users (telegram_id, full_name, phone)
                   VALUES (?, ?, ?)
                   """, (
                       telegram_id or 0,
                       row_dict.get('name', 'Unknown'),
                       row_dict.get('phone', '')
                   ))
    conn.commit()
    return cursor.lastrowid


def _get_course_id(conn: sqlite3.Connection, course_name: str) -> int:
    """Получить ID курса по названию"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM courses WHERE name = ?", (course_name,))
    result = cursor.fetchone()
    return result[0] if result else 1  # По умолчанию первый курс


def _get_training_type_id(conn: sqlite3.Connection, training_type: str) -> int:
    """Получить ID типа обучения"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM training_types WHERE name = ?", (training_type,))
    result = cursor.fetchone()
    return result[0] if result else 1


def _get_schedule_id(conn: sqlite3.Connection, schedule: str) -> int:
    """Получить ID расписания"""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM schedules WHERE name = ?", (schedule,))
    result = cursor.fetchone()
    return result[0] if result else 1


def migrate_other_tables(old_conn: sqlite3.Connection, new_conn: sqlite3.Connection):
    """Мигрировать другие таблицы (feedback, reminders и т.д.)"""
    print("\n📊 Миграция остальных таблиц...")

    # Список таблиц для простой миграции
    simple_tables = ['reminders', 'feedback']

    for table in simple_tables:
        try:
            old_cursor = old_conn.cursor()
            old_cursor.execute(f"SELECT * FROM {table}")
            rows = old_cursor.fetchall()

            if not rows:
                print(f"   ℹ️  Таблица {table} пустая")
                continue

            column_names = [desc[0] for desc in old_cursor.description]

            new_cursor = new_conn.cursor()
            placeholders = ','.join(['?' for _ in column_names])
            new_cursor.executemany(
                f"INSERT INTO {table} ({','.join(column_names)}) VALUES ({placeholders})",
                rows
            )
            new_conn.commit()
            print(f"   ✅ {table}: мигрировано {len(rows)} записей")

        except Exception as e:
            print(f"   ❌ Ошибка при миграции {table}: {e}")


def verify_migration(conn: sqlite3.Connection):
    """Проверить результаты миграции"""
    print("\n🔍 Проверка миграции...")

    cursor = conn.cursor()

    # Проверяем количество записей
    tables = ['users', 'registrations', 'courses', 'training_types', 'schedules']

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   📊 {table}: {count} записей")

    # Проверяем распределение по статусам
    cursor.execute("""
                   SELECT status_code, COUNT(*)
                   FROM registrations
                   GROUP BY status_code
                   """)
    print("\n   📈 Распределение регистраций по статусам:")
    for row in cursor.fetchall():
        print(f"      {row[0]}: {row[1]}")


def migrate_registrations(old_conn: sqlite3.Connection, new_conn: sqlite3.Connection):
    """Мигрировать данные регистраций из множественных таблиц в одну"""
    print("\n📊 Миграция регистраций...")

    # Маппинг старых таблиц на статусы
    table_status_map = {
        'registrations_active': 'active',
        'registrations_trial': 'trial',
        'registrations_studying': 'studying',
        'registrations_frozen': 'frozen',
        'registrations_payment': 'waiting_payment',
        'registrations_completed': 'completed',
        'registrations_other': 'active'  # По умолчанию
    }

    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()

    total_migrated = 0

    # Собираем данные из всех старых таблиц
    for table_name, status in table_status_map.items():
        try:
            # Проверяем существование таблицы
            old_cursor.execute(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table_name}'
            """)
            if not old_cursor.fetchone():
                print(f"   ⚠️  Таблица {table_name} не найдена, пропускаем")
                continue

            # Получаем данные
            old_cursor.execute(f"SELECT * FROM {table_name}")
            rows = old_cursor.fetchall()

            if not rows:
                print(f"   ℹ️  Таблица {table_name} пустая")
                continue

            # Получаем названия колонок
            column_names = [description[0] for description in old_cursor.description]

            migrated_count = 0
            for row in rows:
                row_dict = dict(zip(column_names, row))

                # Сначала создаем/находим пользователя
                user_id = _ensure_user_exists(new_conn, row_dict)

                # Затем создаем регистрацию
                new_cursor.execute("""
                                   INSERT INTO registrations (user_id, course_id, training_type_id, schedule_id,
                                                              status_code, created_at, consultation_time,
                                                              trial_lesson_time, notified, reminder_sent, notes)
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                   """, (
                                       user_id,
                                       _get_course_id(new_conn, row_dict.get('course', '')),
                                       _get_training_type_id(new_conn, row_dict.get('training_type', '')),
                                       _get_schedule_id(new_conn, row_dict.get('schedule', '')),
                                       status,
                                       row_dict.get('created_at', datetime.now()),
                                       row_dict.get('consultation_time'),
                                       row_dict.get('trial_lesson_time'),
                                       row_dict.get('notified', 0),
                                       row_dict.get('reminder_sent', 0),
                                       f"Мигрировано из {table_name}"
                                   ))
                migrated_count += 1

            new_conn.commit()
            total_migrated += migrated_count
            print(f"   ✅ {table_name}: мигрировано {migrated_count} записей")

        except Exception as e:
            print(f"   ❌ Ошибка при миграции {table_name}: {e}")
            new_conn.rollback()

    print(f"\n✅ Всего мигрировано регистраций: {total_migrated}")


class DatabaseMigration:
    def __init__(self, old_db: str = "students.db", new_db: str = "education_center.db"):
        self.old_db = old_db
        self.new_db = new_db
        self.backup_db = f"{old_db}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def create_backup(self):
        """Создать резервную копию текущей БД"""
        if os.path.exists(self.old_db):
            print(f"📦 Создание резервной копии: {self.backup_db}")
            shutil.copy2(self.old_db, self.backup_db)
            print(f"✅ Резервная копия создана")
        else:
            print(f"⚠️  Файл {self.old_db} не найден, копия не создана")

    def run(self):
        """Запустить полную миграцию"""
        print("=" * 60)
        print("🚀 ЗАПУСК МИГРАЦИИ БД")
        print("=" * 60)

        # Шаг 1: Создать backup
        self.create_backup()

        # Шаг 2: Проверить наличие старой БД
        if not os.path.exists(self.old_db):
            print(f"\n❌ Файл {self.old_db} не найден!")
            print(f"💡 Создаю новую БД: {self.new_db}")

            # Создаем новую БД из схемы
            new_conn = sqlite3.connect(self.new_db)
            with open('optimized_schema.sql', 'r', encoding='utf-8') as f:
                new_conn.executescript(f.read())
            new_conn.close()

            print(f"✅ Новая БД создана")
            return

        # Шаг 3: Создать новую БД
        print(f"\n📝 Создание новой структуры: {self.new_db}")
        new_conn = sqlite3.connect(self.new_db)

        with open('optimized_schema.sql', 'r', encoding='utf-8') as f:
            new_conn.executescript(f.read())

        # Шаг 4: Открыть старую БД
        print(f"\n📖 Чтение данных из: {self.old_db}")
        old_conn = sqlite3.connect(self.old_db)

        # Шаг 5: Миграция данных
        migrate_registrations(old_conn, new_conn)
        migrate_other_tables(old_conn, new_conn)

        # Шаг 6: Проверка
        verify_migration(new_conn)

        # Закрываем соединения
        old_conn.close()
        new_conn.close()

        print("\n" + "=" * 60)
        print("✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 60)
        print(f"\n📦 Резервная копия: {self.backup_db}")
        print(f"📊 Новая БД: {self.new_db}")
        print("\n💡 Следующие шаги:")
        print("   1. Обновите config.py: DB_NAME = 'education_center.db'")
        print("   2. Удалите старые файлы БД после проверки")
        print("   3. Обновите handlers для работы с новой структурой")


def main():
    """Точка входа"""
    migration = DatabaseMigration()

    # Запрашиваем подтверждение
    print("\n⚠️  ВНИМАНИЕ: Эта операция изменит структуру БД!")
    print("Резервная копия будет создана автоматически.")

    response = input("\nПродолжить миграцию? (yes/no): ")

    if response.lower() in ['yes', 'y', 'да']:
        migration.run()
    else:
        print("\n❌ Миграция отменена")


if __name__ == "__main__":
    main()
