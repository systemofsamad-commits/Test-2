import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from states.admin_states import AdminStates
from helpers import is_admin, get_db
from config import Config

logger = logging.getLogger(__name__)
router = Router(name="admin_lesson_handlers")
config = Config()


@router.callback_query(F.data == "add_lesson")
async def add_lesson_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления урока"""
    if not is_admin(callback.from_user.id):
        return

    db = get_db()

    # ✅ ИСПРАВЛЕНО: Прямой SQL запрос для получения активных групп
    query = """
            SELECT g.id, \
                   g.name, \
                   g.course_id, \
                   g.teacher_id,
                   c.name as course_name, \
                   t.name as teacher_name
            FROM groups g
                     LEFT JOIN courses c ON g.course_id = c.id
                     LEFT JOIN teachers t ON g.teacher_id = t.id
            WHERE g.is_active = 1
            ORDER BY g.name \
            """
    groups = db.execute_query(query)

    if not groups:
        from keyboards.admin_kb import get_lesson_management_keyboard
        await callback.message.edit_text(
            "❌ Нет доступных групп. Сначала создайте группу.",
            reply_markup=get_lesson_management_keyboard()
        )
        return

    buttons = []
    for group in groups:
        buttons.append([InlineKeyboardButton(
            text=f"👥 {group['name']}",
            callback_data=f"select_lesson_group_{group['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_lesson_add")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await state.set_state(AdminStates.waiting_for_lesson_group)

    await callback.message.edit_text(
        "📖 *Добавление нового урока*\n\n"
        "👥 Выберите группу:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("select_lesson_group_"))
async def select_lesson_group(callback: CallbackQuery, state: FSMContext):
    """Выбор группы для урока"""
    if not is_admin(callback.from_user.id):
        return

    group_id = int(callback.data.replace("select_lesson_group_", ""))

    db = get_db()

    # ✅ ИСПРАВЛЕНО: Прямой SQL запрос для получения группы
    query = """
            SELECT g.id, \
                   g.name, \
                   g.course_id, \
                   g.teacher_id,
                   c.name as course_name, \
                   t.name as teacher_name
            FROM groups g
                     LEFT JOIN courses c ON g.course_id = c.id
                     LEFT JOIN teachers t ON g.teacher_id = t.id
            WHERE g.id = ? \
            """
    results = db.execute_query(query, (group_id,))
    group = results[0] if results else None

    if not group:
        await callback.answer("❌ Группа не найдена.")
        return

    await state.update_data(lesson_group_id=group_id, lesson_group_name=group['name'])
    await state.set_state(AdminStates.waiting_for_lesson_topic)

    from keyboards.admin_kb import get_cancel_keyboard
    await callback.message.edit_text(
        f"👥 Группа: *{group['name']}*\n\n"
        "📝 Введите тему урока:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_lesson_topic)
async def add_lesson_topic_process(message: Message, state: FSMContext):
    """Обработка темы урока"""
    if not is_admin(message.from_user.id):
        return

    if message.text in ["❌ Отмена", "◀️ Назад"]:
        await state.clear()
        from keyboards.admin_kb import get_lesson_management_keyboard
        await message.answer("❌ Добавление урока отменено.",
                             reply_markup=get_lesson_management_keyboard())
        return

    await state.update_data(lesson_topic=message.text)
    await state.set_state(AdminStates.waiting_for_lesson_date)

    from keyboards.admin_kb import get_cancel_keyboard
    await message.answer(
        "📅 Введите дату и время урока (формат: ГГГГ-ММ-ДД ЧЧ:ММ:СС):",
        reply_markup=get_cancel_keyboard()
    )


@router.message(AdminStates.waiting_for_lesson_date)
async def add_lesson_date_process(message: Message, state: FSMContext):
    """Обработка даты урока и сохранение"""
    if not is_admin(message.from_user.id):
        return

    if message.text in ["❌ Отмена", "◀️ Назад"]:
        await state.clear()
        from keyboards.admin_kb import get_lesson_management_keyboard
        await message.answer("❌ Добавление урока отменено.",
                             reply_markup=get_lesson_management_keyboard())
        return

    # Валидация даты
    try:
        from datetime import datetime
        datetime.strptime(message.text, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        from keyboards.admin_kb import get_cancel_keyboard
        await message.answer(
            "❌ Неверный формат даты. Используйте ГГГГ-ММ-ДД ЧЧ:ММ:СС:",
            reply_markup=get_cancel_keyboard()
        )
        return

    data = await state.get_data()

    db = get_db()

    # ✅ ИСПРАВЛЕНО: Прямой SQL запрос для получения группы
    query = """
            SELECT g.id, \
                   g.name, \
                   g.course_id, \
                   g.teacher_id,
                   c.name as course_name, \
                   t.name as teacher_name
            FROM groups g
                     LEFT JOIN courses c ON g.course_id = c.id
                     LEFT JOIN teachers t ON g.teacher_id = t.id
            WHERE g.id = ? \
            """
    results = db.execute_query(query, (data['lesson_group_id'],))
    group = results[0] if results else None

    if not group or not group.get('teacher_id'):
        from keyboards.admin_kb import get_lesson_management_keyboard
        await message.answer(
            "❌ Ошибка: у группы нет назначенного преподавателя.",
            reply_markup=get_lesson_management_keyboard()
        )
        await state.clear()
        return

    # ✅ ИСПРАВЛЕНО: Прямой SQL INSERT для создания урока
    try:
        query = """
                INSERT INTO lessons (group_id, teacher_id, topic, lesson_date, duration_minutes, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now')) \
                """
        lesson_id = db.execute_insert(query, (
            data['lesson_group_id'],
            group['teacher_id'],
            data['lesson_topic'],
            message.text,
            60
        ))
        success = lesson_id is not None
    except Exception as e:
        logger.error(f"Error creating lesson: {e}", exc_info=True)
        success = False

    if success:
        from keyboards.admin_kb import get_lesson_management_keyboard
        await message.answer(
            f"✅ Урок *{data['lesson_topic']}* успешно добавлен!\n\n"
            f"👥 Группа: {data['lesson_group_name']}\n"
            f"👨‍🏫 Преподаватель: {group.get('teacher_name', 'Не указан')}\n"
            f"📅 Дата: {message.text}",
            parse_mode="Markdown",
            reply_markup=get_lesson_management_keyboard()
        )
    else:
        from keyboards.admin_kb import get_lesson_management_keyboard
        await message.answer(
            f"❌ Ошибка при добавлении урока.",
            reply_markup=get_lesson_management_keyboard()
        )

    await state.clear()


@router.callback_query(F.data == "cancel_lesson_add")
async def cancel_lesson_add(callback: CallbackQuery, state: FSMContext):
    """Отмена добавления урока"""
    if not is_admin(callback.from_user.id):
        return

    await state.clear()
    from keyboards.admin_kb import get_lesson_management_keyboard
    await callback.message.edit_text(
        "❌ Добавление урока отменено.",
        reply_markup=get_lesson_management_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "list_lessons")
async def list_lessons(callback: CallbackQuery):
    """Показать список всех уроков"""
    if not is_admin(callback.from_user.id):
        return

    db = get_db()

    # ✅ ИСПРАВЛЕНО: Прямой SQL запрос для получения уроков
    try:
        query = """
                SELECT l.id, \
                       l.topic, \
                       l.lesson_date, \
                       l.duration_minutes,
                       g.name as group_name, \
                       t.name as teacher_name
                FROM lessons l
                         LEFT JOIN groups g ON l.group_id = g.id
                         LEFT JOIN teachers t ON l.teacher_id = t.id
                ORDER BY l.lesson_date DESC
                LIMIT 20 \
                """
        lessons = db.execute_query(query)
    except Exception as e:
        logger.error(f"Error fetching lessons: {e}", exc_info=True)
        lessons = []

    if not lessons:
        from keyboards.admin_kb import get_lesson_management_keyboard
        await callback.message.edit_text(
            "❌ Нет запланированных уроков.",
            reply_markup=get_lesson_management_keyboard()
        )
        return

    lesson_list = "📖 *Список уроков:*\n\n"

    for i, lesson in enumerate(lessons, 1):
        lesson_date = lesson['lesson_date'][:16] if lesson.get('lesson_date') else 'Не указана'
        lesson_info = (
            f"{i}. *{lesson['topic']}*\n"
            f"   🆔 ID: {lesson['id']}\n"
            f"   👥 Группа: {lesson.get('group_name', 'Не указана')}\n"
            f"   👨‍🏫 Преподаватель: {lesson.get('teacher_name', 'Не указан')}\n"
            f"   📅 Дата: {lesson_date}\n"
            f"   ⏱️ Длительность: {lesson.get('duration_minutes', 60)} мин\n"
        )

        lesson_list += lesson_info + "\n"

    from keyboards.admin_kb import get_lesson_management_keyboard
    await callback.message.edit_text(
        lesson_list,
        parse_mode="Markdown",
        reply_markup=get_lesson_management_keyboard()
    )
    await callback.answer()