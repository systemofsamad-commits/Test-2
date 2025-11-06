import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from states.admin_states import AdminStates
from database import Database
from helpers import is_admin
from config import Config

logger = logging.getLogger(__name__)
router = Router(name="admin_management_handlers")
config = Config()
db = Database(config.DB_NAME)


# ============ УПРАВЛЕНИЕ ПРЕПОДАВАТЕЛЯМИ ============

@router.callback_query(F.data == "add_teacher")
async def add_teacher_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления преподавателя"""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_teacher_name)
    from keyboards.admin_kb import get_cancel_keyboard
    await callback.message.edit_text(
        "👨‍🏫 *Добавление преподавателя*\n\n"
        "Введите ФИО преподавателя:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_teacher_name)
async def add_teacher_name_process(message: Message, state: FSMContext):
    """Обработка имени преподавателя"""
    if not is_admin(message.from_user.id):
        return

    if message.text in ["❌ Отмена", "◀️ Назад"]:
        await state.clear()
        from keyboards.admin_kb import get_admin_teachers_menu
        await message.answer("❌ Добавление преподавателя отменено.",
                             reply_markup=get_admin_teachers_menu())
        return

    await state.update_data(teacher_name=message.text)
    await state.set_state(AdminStates.waiting_for_teacher_phone)
    from keyboards.admin_kb import get_cancel_keyboard
    await message.answer("📞 Введите номер телефона преподавателя:", reply_markup=get_cancel_keyboard())


@router.message(AdminStates.waiting_for_teacher_phone)
async def add_teacher_phone_process(message: Message, state: FSMContext):
    """Обработка телефона преподавателя"""
    if not is_admin(message.from_user.id):
        return

    if message.text in ["❌ Отмена", "◀️ Назад"]:
        await state.clear()
        from keyboards.admin_kb import get_admin_teachers_menu
        await message.answer("❌ Добавление преподавателя отменено.",
                             reply_markup=get_admin_teachers_menu())
        return

    phone = message.text.strip()
    if len(phone) < 5:
        from keyboards.admin_kb import get_cancel_keyboard
        await message.answer(
            "❌ Номер телефона слишком короткий. Введите корректный номер:",
            reply_markup=get_cancel_keyboard()
        )
        return

    await state.update_data(teacher_phone=phone)

    buttons = [
        [InlineKeyboardButton(text="✅ Пропустить", callback_data="skip_teacher_email")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_teacher_add")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await state.set_state(AdminStates.waiting_for_teacher_email)
    await message.answer(
        "📧 Введите email преподавателя (или нажмите 'Пропустить'):",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "skip_teacher_email")
async def skip_teacher_email(callback: CallbackQuery, state: FSMContext):
    """Пропуск email и сохранение преподавателя"""
    if not is_admin(callback.from_user.id):
        return

    data = await state.get_data()

    # Сохраняем преподавателя без email
    success = db.add_teacher(
        name=data['teacher_name'],
        phone=data['teacher_phone'],
        email=None
    )

    if success:
        from keyboards.admin_kb import get_admin_teachers_menu
        await callback.message.edit_text(
            f"✅ Преподаватель *{data['teacher_name']}* успешно добавлен!",
            parse_mode="Markdown",
            reply_markup=get_admin_teachers_menu()
        )
    else:
        from keyboards.admin_kb import get_admin_teachers_menu
        await callback.message.edit_text(
            "❌ Ошибка при добавлении преподавателя",
            reply_markup=get_admin_teachers_menu()
        )

    await state.clear()
    await callback.answer()


@router.message(AdminStates.waiting_for_teacher_email)
async def add_teacher_email_process(message: Message, state: FSMContext):
    """Обработка email преподавателя"""
    if not is_admin(message.from_user.id):
        return

    if message.text in ["❌ Отмена", "◀️ Назад"]:
        await state.clear()
        from keyboards.admin_kb import get_admin_teachers_menu
        await message.answer("❌ Добавление преподавателя отменено.",
                             reply_markup=get_admin_teachers_menu())
        return

    data = await state.get_data()

    # Сохраняем преподавателя с email
    success = db.add_teacher(
        name=data['teacher_name'],
        phone=data['teacher_phone'],
        email=message.text
    )

    if success:
        from keyboards.admin_kb import get_admin_teachers_menu
        await message.answer(
            f"✅ Преподаватель *{data['teacher_name']}* успешно добавлен!",
            parse_mode="Markdown",
            reply_markup=get_admin_teachers_menu()
        )
    else:
        from keyboards.admin_kb import get_admin_teachers_menu
        await message.answer(
            "❌ Ошибка при добавлении преподавателя",
            reply_markup=get_admin_teachers_menu()
        )

    await state.clear()


@router.callback_query(F.data == "cancel_teacher_add")
async def cancel_teacher_add(callback: CallbackQuery, state: FSMContext):
    """Отмена добавления преподавателя"""
    if not is_admin(callback.from_user.id):
        return

    await state.clear()
    from keyboards.admin_kb import get_admin_teachers_menu
    await callback.message.edit_text(
        "❌ Добавление преподавателя отменено.",
        reply_markup=get_admin_teachers_menu()
    )
    await callback.answer()


# ============ УПРАВЛЕНИЕ ГРУППАМИ ============

@router.callback_query(F.data == "add_group")
async def add_group_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления группы"""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_group_name)
    from keyboards.admin_kb import get_cancel_keyboard
    await callback.message.edit_text(
        "👥 *Добавление новой группы*\n\n"
        "Введите название группы:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_group_name)
async def add_group_name_process(message: Message, state: FSMContext):
    """Обработка названия группы"""
    if not is_admin(message.from_user.id):
        return

    if message.text in ["❌ Отмена", "◀️ Назад"]:
        await state.clear()
        from keyboards.admin_kb import get_group_management_keyboard
        await message.answer("❌ Добавление группы отменено.",
                             reply_markup=get_group_management_keyboard())
        return

    await state.update_data(group_name=message.text)

    # Получаем список курсов для выбора
    courses = db.get_active_courses()
    if not courses:
        from keyboards.admin_kb import get_group_management_keyboard
        await message.answer(
            "❌ Нет доступных курсов. Сначала добавьте курс.",
            reply_markup=get_group_management_keyboard()
        )
        await state.clear()
        return

    # Создаем клавиатуру с курсами
    buttons = []
    for course in courses:
        buttons.append([InlineKeyboardButton(
            text=f"📚 {course['name']}",
            callback_data=f"select_course_{course['id']}"
        )])
    buttons.append([InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="cancel_group_add"
    )])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await state.set_state(AdminStates.waiting_for_group_course)
    await message.answer(
        "📚 Выберите курс для группы:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("select_course_"))
async def select_group_course(callback: CallbackQuery, state: FSMContext):
    """Выбор курса для группы"""
    if not is_admin(callback.from_user.id):
        return

    course_id = int(callback.data.replace("select_course_", ""))

    courses = db.get_active_courses()
    selected_course = next((c for c in courses if c['id'] == course_id), None)

    if not selected_course:
        await callback.answer("❌ Курс не найден.")
        return

    await state.update_data(group_course_id=course_id, group_course_name=selected_course['name'])

    # Получаем список преподавателей для выбора
    teachers = db.get_active_teachers()
    if not teachers:
        from keyboards.admin_kb import get_group_management_keyboard
        await callback.message.edit_text(
            "❌ Нет доступных преподавателей. Сначала добавьте преподавателя.",
            reply_markup=get_group_management_keyboard()
        )
        await state.clear()
        return

    # Создаем клавиатуру с преподавателями
    buttons = []
    for teacher in teachers:
        buttons.append([InlineKeyboardButton(
            text=f"👨‍🏫 {teacher['name']}",
            callback_data=f"select_teacher_{teacher['id']}"
        )])
    buttons.append([InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="cancel_group_add"
    )])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await state.set_state(AdminStates.waiting_for_group_teacher)
    await callback.message.edit_text(
        f"📚 Курс: *{selected_course['name']}*\n\n"
        "👨‍🏫 Выберите преподавателя для группы:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("select_teacher_"))
async def select_group_teacher(callback: CallbackQuery, state: FSMContext):
    """Выбор преподавателя для группы и сохранение"""
    if not is_admin(callback.from_user.id):
        return

    teacher_id = int(callback.data.replace("select_teacher_", ""))

    teachers = db.get_active_teachers()
    selected_teacher = next((t for t in teachers if t['id'] == teacher_id), None)

    if not selected_teacher:
        await callback.answer("❌ Преподаватель не найден.")
        return

    data = await state.get_data()

    # Сохраняем группу
    success = db.add_group(
        name=data['group_name'],
        course_id=data['group_course_id'],
        teacher_id=teacher_id
    )

    if success:
        from keyboards.admin_kb import get_group_management_keyboard
        await callback.message.edit_text(
            f"✅ Группа *{data['group_name']}* успешно создана!\n\n"
            f"📚 Курс: {data['group_course_name']}\n"
            f"👨‍🏫 Преподаватель: {selected_teacher['name']}",
            parse_mode="Markdown",
            reply_markup=get_group_management_keyboard()
        )
    else:
        from keyboards.admin_kb import get_group_management_keyboard
        await callback.message.edit_text(
            "❌ Ошибка при создании группы",
            reply_markup=get_group_management_keyboard()
        )

    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel_group_add")
async def cancel_group_add(callback: CallbackQuery, state: FSMContext):
    """Отмена добавления группы"""
    if not is_admin(callback.from_user.id):
        return

    await state.clear()
    from keyboards.admin_kb import get_group_management_keyboard
    await callback.message.edit_text(
        "❌ Добавление группы отменено.",
        reply_markup=get_group_management_keyboard()
    )
    await callback.answer()


# ============ УПРАВЛЕНИЕ КУРСАМИ ============

@router.callback_query(F.data == "add_course")
async def add_course_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления курса"""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_course_name)
    from keyboards.admin_kb import get_cancel_keyboard
    await callback.message.edit_text(
        "📚 *Добавление нового курса*\n\n"
        "Введите название курса:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_course_name)
async def add_course_name_process(message: Message, state: FSMContext):
    """Обработка названия курса"""
    if not is_admin(message.from_user.id):
        return

    if message.text in ["❌ Отмена", "◀️ Назад"]:
        await state.clear()
        from keyboards.admin_kb import get_admin_courses_menu
        await message.answer("❌ Добавление курса отменено.",
                             reply_markup=get_admin_courses_menu())
        return

    await state.update_data(course_name=message.text)
    await state.set_state(AdminStates.waiting_for_course_description)

    buttons = [
        [InlineKeyboardButton(text="✅ Пропустить", callback_data="skip_course_description")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_course_add")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer("📝 Введите описание курса (или нажмите 'Пропустить'):", reply_markup=keyboard)


@router.callback_query(F.data == "skip_course_description")
async def skip_course_description(callback: CallbackQuery, state: FSMContext):
    """Пропуск описания и сохранение курса"""
    if not is_admin(callback.from_user.id):
        return

    data = await state.get_data()

    # Сохраняем курс без описания
    success = db.add_course(
        name=data['course_name'],
        description=None
    )

    if success:
        from keyboards.admin_kb import get_admin_courses_menu
        await callback.message.edit_text(
            f"✅ Курс *{data['course_name']}* успешно добавлен!",
            parse_mode="Markdown",
            reply_markup=get_admin_courses_menu()
        )
    else:
        from keyboards.admin_kb import get_admin_courses_menu
        await callback.message.edit_text(
            "❌ Ошибка при добавлении курса",
            reply_markup=get_admin_courses_menu()
        )

    await state.clear()
    await callback.answer()


@router.message(AdminStates.waiting_for_course_description)
async def add_course_description_process(message: Message, state: FSMContext):
    """Обработка описания курса"""
    if not is_admin(message.from_user.id):
        return

    if message.text in ["❌ Отмена", "◀️ Назад"]:
        await state.clear()
        from keyboards.admin_kb import get_admin_courses_menu
        await message.answer("❌ Добавление курса отменено.",
                             reply_markup=get_admin_courses_menu())
        return

    data = await state.get_data()

    # Сохраняем курс с описанием
    success = db.add_course(
        name=data['course_name'],
        description=message.text
    )

    if success:
        from keyboards.admin_kb import get_admin_courses_menu
        await message.answer(
            f"✅ Курс *{data['course_name']}* успешно добавлен!",
            parse_mode="Markdown",
            reply_markup=get_admin_courses_menu()
        )
    else:
        from keyboards.admin_kb import get_admin_courses_menu
        await message.answer(
            "❌ Ошибка при добавлении курса",
            reply_markup=get_admin_courses_menu()
        )

    await state.clear()


@router.callback_query(F.data == "cancel_course_add")
async def cancel_course_add(callback: CallbackQuery, state: FSMContext):
    """Отмена добавления курса"""
    if not is_admin(callback.from_user.id):
        return

    await state.clear()
    from keyboards.admin_kb import get_admin_courses_menu
    await callback.message.edit_text(
        "❌ Добавление курса отменено.",
        reply_markup=get_admin_courses_menu()
    )
    await callback.answer()
