import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from states.admin_states import AdminStates
from database import Database
from helpers import is_admin
from config import Config

logger = logging.getLogger(__name__)
router = Router(name="admin_lesson_handlers")
config = Config()
db = Database(config.DB_NAME)


@router.callback_query(F.data == "add_lesson")
async def add_lesson_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления урока"""
    if not is_admin(callback.from_user.id):
        return

    groups = db.get_active_groups()
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

    groups = db.get_active_groups()
    selected_group = next((g for g in groups if g['id'] == group_id), None)

    if not selected_group:
        await callback.answer("❌ Группа не найдена.")
        return

    await state.update_data(lesson_group_id=group_id, lesson_group_name=selected_group['name'])
    await state.set_state(AdminStates.waiting_for_lesson_topic)

    from keyboards.admin_kb import get_cancel_keyboard
    await callback.message.edit_text(
        f"👥 Группа: *{selected_group['name']}*\n\n"
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

    # Получаем ID преподавателя из группы
    groups = db.get_all_groups()
    selected_group = next((g for g in groups if g['id'] == data['lesson_group_id']), None)

    if not selected_group or not selected_group['teacher_id']:
        from keyboards.admin_kb import get_lesson_management_keyboard
        await message.answer(
            "❌ Ошибка: у группы нет назначенного преподавателя.",
            reply_markup=get_lesson_management_keyboard()
        )
        await state.clear()
        return

    # Сохраняем урок
    success = db.add_lesson(
        group_id=data['lesson_group_id'],
        teacher_id=selected_group['teacher_id'],
        topic=data['lesson_topic'],
        lesson_date=message.text,
        duration_minutes=60
    )

    if success:
        from keyboards.admin_kb import get_lesson_management_keyboard
        await message.answer(
            f"✅ Урок *{data['lesson_topic']}* успешно добавлен!\n\n"
            f"👥 Группа: {data['lesson_group_name']}\n"
            f"👨‍🏫 Преподаватель: {selected_group['teacher_name']}\n"
            f"📅 Дата: {message.text}",
            parse_mode="Markdown",
            reply_markup=get_lesson_management_keyboard()
        )
    else:
        from keyboards.admin_kb import get_lesson_management_keyboard
        await message.answer(
            f"❌ Ошибка при добавлении урока {data['lesson_topic']}.",
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

    lessons = db.get_all_lessons()

    if not lessons:
        from keyboards.admin_kb import get_lesson_management_keyboard
        await callback.message.edit_text(
            "❌ Нет запланированных уроков.",
            reply_markup=get_lesson_management_keyboard()
        )
        return

    lesson_list = "📖 *Список уроков:*\n\n"

    for i, lesson in enumerate(lessons, 1):
        lesson_date = lesson['lesson_date'][:16]  # Обрезаем секунды
        lesson_info = (
            f"{i}. *{lesson['topic']}*\n"
            f"   🆔 ID: {lesson['id']}\n"
            f"   👥 Группа: {lesson['group_name']}\n"
            f"   👨‍🏫 Преподаватель: {lesson['teacher_name']}\n"
            f"   📅 Дата: {lesson_date}\n"
            f"   ⏱️ Длительность: {lesson['duration_minutes']} мин\n"
        )

        lesson_list += lesson_info + "\n"

    from keyboards.admin_kb import get_lesson_management_keyboard
    await callback.message.edit_text(
        lesson_list,
        parse_mode="Markdown",
        reply_markup=get_lesson_management_keyboard()
    )
    await callback.answer()