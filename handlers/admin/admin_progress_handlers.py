import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.student_states import StudentStates
from helpers import is_admin, get_db
from config import Config

logger = logging.getLogger(__name__)
router = Router(name="admin_progress_handlers")
config = Config()


# Обновление прогресса
@router.callback_query(F.data.startswith("update_progress_"))
async def handle_update_progress(callback: CallbackQuery, state: FSMContext):
    """Обновление прогресса студента"""
    if not is_admin(callback.from_user.id):
        return

    registration_id = int(callback.data.split("_")[2])

    db = get_db()

    # ✅ ИСПРАВЛЕНО: Прямой SQL запрос
    query = """
            SELECT r.id, \
                   r.status_code, \
                   r.notes,
                   r.full_name as name, \
                   r.phone,
                   c.name      as course_name
            FROM registrations r
                     LEFT JOIN courses c ON r.course_id = c.id
            WHERE r.id = ? \
            """
    results = db.execute_query(query, (registration_id,))
    reg = results[0] if results else None

    if not reg:
        await callback.answer("Студент не найден", show_alert=True)
        return

    await state.update_data(registration_id=registration_id)

    from keyboards.admin_kb import get_progress_update_keyboard
    await callback.message.edit_text(
        f"📊 Обновление прогресса для {reg['name']}\n"
        f"Текущий прогресс: {reg.get('notes', 'Не указан')}",
        reply_markup=get_progress_update_keyboard(registration_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("progress_"))
async def handle_progress_selection(callback: CallbackQuery, state: FSMContext):
    """Выбор типа прогресса"""
    if not is_admin(callback.from_user.id):
        return

    data_parts = callback.data.split("_")
    progress_type = data_parts[1]
    registration_id = int(data_parts[2])

    progress_map = {
        'excellent': 'Отлично',
        'good': 'Хорошо',
        'fair': 'Удовлетворительно',
        'help': 'Требуется помощь'
    }

    if progress_type == 'custom':
        await callback.message.answer("Введите комментарий к прогрессу:")
        await state.update_data(registration_id=registration_id)
        await state.set_state(StudentStates.waiting_custom_progress)
    else:
        progress_text = progress_map.get(progress_type, progress_type)

        db = get_db()

        # ✅ ИСПРАВЛЕНО: Прямой SQL UPDATE для добавления заметки
        try:
            query = """
                    UPDATE registrations
                    SET notes      = CASE \
                                         WHEN notes IS NULL OR notes = '' THEN ? \
                                         ELSE notes || '\n' || ?
                        END,
                        updated_at = datetime('now')
                    WHERE id = ? \
                    """
            note_text = f"Прогресс: {progress_text}"
            db.execute_update(query, (note_text, note_text, registration_id))
        except Exception as e:
            logger.error(f"Error adding note: {e}", exc_info=True)

        # ✅ ИСПРАВЛЕНО: Прямой SQL SELECT
        query = """
                SELECT r.id, \
                       r.status_code, \
                       r.notes,
                       r.full_name as name, \
                       r.phone,
                       c.name      as course_name
                FROM registrations r
                         LEFT JOIN courses c ON r.course_id = c.id
                WHERE r.id = ? \
                """
        results = db.execute_query(query, (registration_id,))
        reg = results[0] if results else None

        if reg:
            from keyboards.admin_kb import get_student_actions_keyboard
            await callback.message.edit_text(
                f"✅ Прогресс обновлен: {progress_text}\n"
                f"Для студента: {reg['name']}",
                reply_markup=get_student_actions_keyboard(
                    registration_id,
                    reg['status_code']
                )
            )

    await callback.answer()


@router.message(StudentStates.waiting_custom_progress)
async def handle_custom_progress_input(message: Message, state: FSMContext):
    """Обработка пользовательского прогресса"""
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    registration_id = data.get('registration_id')

    db = get_db()

    # ✅ ИСПРАВЛЕНО: Прямой SQL UPDATE для добавления заметки
    try:
        query = """
                UPDATE registrations
                SET notes      = CASE \
                                     WHEN notes IS NULL OR notes = '' THEN ? \
                                     ELSE notes || '\n' || ?
                    END,
                    updated_at = datetime('now')
                WHERE id = ? \
                """
        note_text = f"Прогресс: {message.text}"
        db.execute_update(query, (note_text, note_text, registration_id))
    except Exception as e:
        logger.error(f"Error adding note: {e}", exc_info=True)

    # ✅ ИСПРАВЛЕНО: Прямой SQL SELECT
    query = """
            SELECT r.id, \
                   r.status_code, \
                   r.notes,
                   r.full_name as name, \
                   r.phone,
                   c.name      as course_name
            FROM registrations r
                     LEFT JOIN courses c ON r.course_id = c.id
            WHERE r.id = ? \
            """
    results = db.execute_query(query, (registration_id,))
    reg = results[0] if results else None

    if reg:
        from keyboards.admin_kb import get_student_actions_keyboard
        await message.answer(
            f"✅ Прогресс обновлен: {message.text}\n"
            f"Для студента: {reg['name']}",
            reply_markup=get_student_actions_keyboard(
                registration_id,
                reg['status_code']
            )
        )

    await state.clear()


@router.callback_query(F.data.startswith("student_contacts_"))
async def handle_student_contacts(callback: CallbackQuery):
    """Показать контакты студента"""
    if not is_admin(callback.from_user.id):
        return

    registration_id = int(callback.data.split("_")[2])

    db = get_db()

    # ✅ ИСПРАВЛЕНО: Прямой SQL SELECT
    query = """
            SELECT r.id, \
                   r.status_code, \
                   r.notes,
                   r.full_name as name, \
                   r.phone, \
                   r.email,
                   u.telegram_id,
                   c.name      as course_name
            FROM registrations r
                     LEFT JOIN users u ON r.user_id = u.id
                     LEFT JOIN courses c ON r.course_id = c.id
            WHERE r.id = ? \
            """
    results = db.execute_query(query, (registration_id,))
    reg = results[0] if results else None

    if not reg:
        await callback.answer("Студент не найден", show_alert=True)
        return

    contacts_text = f"""
📞 Контакты студента:

👤 Имя: {reg['name']}
📱 Телефон: {reg.get('phone', 'Не указан')}
📧 Email: {reg.get('email', 'Не указан')}
💬 Telegram ID: {reg.get('telegram_id', 'Не указан')}

ID: {registration_id}
    """

    await callback.message.answer(contacts_text)
    await callback.answer()


@router.callback_query(F.data.startswith("full_info_"))
async def handle_full_info(callback: CallbackQuery):
    """Полная информация о студенте"""
    if not is_admin(callback.from_user.id):
        return

    registration_id = int(callback.data.split("_")[2])

    db = get_db()

    # ✅ ИСПРАВЛЕНО: Прямой SQL SELECT
    query = """
            SELECT r.id, \
                   r.status_code, \
                   r.notes, \
                   r.created_at, \
                   r.updated_at,
                   r.full_name as name, \
                   r.phone, \
                   r.email,
                   u.telegram_id,
                   c.name      as course_name
            FROM registrations r
                     LEFT JOIN users u ON r.user_id = u.id
                     LEFT JOIN courses c ON r.course_id = c.id
            WHERE r.id = ? \
            """
    results = db.execute_query(query, (registration_id,))
    reg = results[0] if results else None

    if not reg:
        await callback.answer("Студент не найден", show_alert=True)
        return

    full_info = f"""
📋 Полная информация о студенте:

👤 Основное:
- Имя: {reg['name']}
- ID: {registration_id}
- Статус: {config.STATUSES.get(reg['status_code'], reg['status_code'])}

📞 Контакты:
- Телефон: {reg.get('phone', 'Не указан')}
- Email: {reg.get('email', 'Не указан')}
- Telegram ID: {reg.get('telegram_id', 'Не указан')}

🎓 Обучение:
- Курс: {reg.get('course_name', 'Не указан')}
- Прогресс: {reg.get('notes', 'Не указан')}

📅 Даты:
- Зарегистрирован: {reg.get('created_at', 'Не указана')}
- Последнее обновление: {reg.get('updated_at', 'Не указано')}
    """

    await callback.message.answer(full_info)
    await callback.answer()