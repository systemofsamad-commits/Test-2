"""
Скрипт для автоматического исправления user_handlers.py
Исправляет db.get_user_registrations() на правильный код
"""
import re


def fix_user_handlers():
    """Исправить user_handlers.py"""

    file_path = "handlers/user_handlers.py"

    print("🔧 Исправление user_handlers.py...")
    print()

    # Читаем файл
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # ИСПРАВЛЕНИЕ 1: Заменяем db.get_user_registrations()
    old_code = r'registrations = db\.get_user_registrations\(callback\.from_user\.id\)'

    new_code = '''# Получаем user_id по telegram_id
    query_user = "SELECT id FROM users WHERE telegram_id = ?"
    user_rows = db.execute_query(query_user, (callback.from_user.id,))
    if not user_rows:
        await callback.message.edit_text("Вы еще не зарегистрированы.", reply_markup=get_main_keyboard())
        return

    user_id = user_rows[0]['id']

    # Получаем регистрации пользователя
    registrations = db.registrations.get_by_user_id(user_id)'''

    content = re.sub(old_code, new_code, content)

    count1 = content.count('get_by_user_id')
    print(f"✅ Заменено вхождений db.get_user_registrations(): {count1}")

    # ИСПРАВЛЕНИЕ 2: Заменяем reg.attribute на reg['attribute']
    # Список замен
    replacements = [
        (r'reg\.id', "reg['id']"),
        (r'reg\.course\b', "reg['course_name']"),
        (r'reg\.training_type', "reg['training_type_name']"),
        (r'reg\.schedule', "reg['schedule_name']"),
        (r'reg\.price', "reg['price']"),
        (r'reg\.created_at', "reg['created_at']"),
        (r'reg\.status', "reg['status_code']"),
        (r'reg\.progress', "reg.get('notes', 'Нет данных')"),
    ]

    for old, new in replacements:
        before_count = len(re.findall(old, content))
        content = re.sub(old, new, content)
        after_count = len(re.findall(old, content))
        replaced = before_count - after_count
        if replaced > 0:
            print(f"✅ Заменено {old} → {new}: {replaced} раз")

    # Проверяем что были изменения
    if content == original_content:
        print("⚠️  Файл не изменился. Возможно уже исправлен?")
        return False

    # Сохраняем backup
    backup_path = file_path + ".backup"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original_content)
    print(f"📦 Backup сохранен: {backup_path}")

    # Сохраняем исправленный файл
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print()
    print("✅ user_handlers.py успешно исправлен!")
    print()
    print("🎯 Теперь запусти бота:")
    print("   python main.py")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 АВТОМАТИЧЕСКОЕ ИСПРАВЛЕНИЕ user_handlers.py")
    print("=" * 60)
    print()

    try:
        fix_user_handlers()
    except FileNotFoundError:
        print("❌ Файл handlers/user_handlers.py не найден!")
        print("   Запусти скрипт из корня проекта (D:\\Phyton\\Test-2)")
    except Exception as e:
        print(f"❌ Ошибка: {e}")