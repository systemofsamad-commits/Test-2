import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Config
from database import Database
from helpers import is_admin
from states.admin_states import AdminStates

logger = logging.getLogger(__name__)
router = Router(name="admin_student_handlers")
config = Config()
db = Database(config.DB_NAME)


# ============ ПРОСМОТР СТУДЕНТОВ ПО СТАТУСАМ ============

@router.callback_query(F.data.startswith("view_students_"))
async def view_students_by_status(callback: CallbackQuery):
    """Просмотр студентов по статусу"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    status = callback.data.replace("view_students_", "")

    status_map = {
        'active': 'active',
        'trial': 'trial',
        'studying': 'studying',
        'frozen': 'frozen',
        'payment': 'waiting_payment',
        'completed': 'completed'
    }

    db_status = status_map.get(status, status)
    students = db.get_students_by_status(db_status)

    status_names = {
        'active': '🟢 Активные',
        'trial': '🟡 Пробный урок',
        'studying': '🔵 Обучаются',
        'frozen': '⚪ Заморожены',
        'waiting_payment': '🟠 Ожидание оплаты',
        'completed': '🟣 Завершили'
    }

    status_name = status_names.get(db_status, db_status)

    if not students:
        from keyboards.admin_kb import get_admin_students_menu
        await callback.message.edit_text(
            f"{status_name}\n\n"
            "❌ Нет студентов в этой категории",
            reply_markup=get_admin_students_menu()
        )
        await callback.answer()
        return

    # Показываем первого студента
    student = students[0]
    status_text = config.STATUSES.get(student.status, student.status)

    info_text = (
        f"📋 *Студенты: {status_name}*\n"
        f"Всего: {len(students)}\n\n"
        f"👤 *Студент 1/{len(students)}*\n\n"
        f"📛 Имя: {student.name}\n"
        f"📞 Телефон: {student.phone}\n"
        f"🎯 Курс: {student.course}\n"
        f"📊 Статус: {status_text}\n"
        f"🎓 Тип обучения: {student.training_type}\n"
        f"⏰ Расписание: {student.schedule}\n"
        f"💰 Цена: {student.price}\n"
        f"🆔 ID: {student.id}\n"
    )

    if hasattr(student, 'progress') and student.progress:
        info_text += f"📊 Прогресс: {student.progress}\n"

    from keyboards.admin_kb import get_student_actions_keyboard
    await callback.message.edit_text(
        info_text,
        parse_mode="Markdown",
        reply_markup=get_student_actions_keyboard(student.id, student.status, student.name)
    )
    await callback.answer()


# ============ ПОИСК СТУДЕНТА ============

@router.callback_query(F.data == "find_student_by_id")
async def find_student_by_id_start(callback: CallbackQuery, state: FSMContext):
    """Начать поиск студента по ID"""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_student_id)
    from keyboards.admin_kb import get_cancel_keyboard
    await callback.message.edit_text(
        "🔍 *Поиск студента по ID*\n\n"
        "Введите ID студента:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_student_id)
async def find_student_by_id_process(message: Message, state: FSMContext):
    """Обработка поиска студента по ID"""
    if not is_admin(message.from_user.id):
        return

    if message.text in ["❌ Отмена", "◀️ Назад"]:
        await state.clear()
        from keyboards.admin_kb import get_admin_students_menu
        await message.answer("❌ Поиск отменён", reply_markup=get_admin_students_menu())
        return

    try:
        student_id = int(message.text)
        student = db.get_student_by_id(student_id)

        if not student:
            from keyboards.admin_kb import get_cancel_keyboard
            await message.answer(
                f"❌ Студент с ID {student_id} не найден\n\n"
                "Попробуйте другой ID:",
                reply_markup=get_cancel_keyboard()
            )
            return

        status_text = config.STATUSES.get(student.status, student.status)
        info_text = (
            f"✅ *Студент найден!*\n\n"
            f"👤 Имя: {student.name}\n"
            f"📞 Телефон: {student.phone}\n"
            f"🎯 Курс: {student.course}\n"
            f"📊 Статус: {status_text}\n"
            f"🎓 Тип обучения: {student.training_type}\n"
            f"⏰ Расписание: {student.schedule}\n"
            f"💰 Цена: {student.price}\n"
            f"🆔 ID: {student.id}\n"
        )

        from keyboards.admin_kb import get_student_actions_keyboard
        await message.answer(
            info_text,
            parse_mode="Markdown",
            reply_markup=get_student_actions_keyboard(student.id, student.status, student.name)
        )
        await state.clear()

    except ValueError:
        from keyboards.admin_kb import get_cancel_keyboard
        await message.answer(
            "❌ Неверный формат ID. Введите число:",
            reply_markup=get_cancel_keyboard()
        )


@router.callback_query(F.data == "find_student_by_phone")
async def find_student_by_phone_start(callback: CallbackQuery, state: FSMContext):
    """Начать поиск студента по телефону"""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_student_phone)
    from keyboards.admin_kb import get_cancel_keyboard
    await callback.message.edit_text(
        "🔍 *Поиск студента по телефону*\n\n"
        "Введите номер телефона:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_student_phone)
async def find_student_by_phone_process(message: Message, state: FSMContext):
    """Обработка поиска студента по телефону"""
    if not is_admin(message.from_user.id):
        return

    if message.text in ["❌ Отмена", "◀️ Назад"]:
        await state.clear()
        from keyboards.admin_kb import get_admin_students_menu
        await message.answer("❌ Поиск отменён", reply_markup=get_admin_students_menu())
        return

    phone = message.text.strip()
    students = db.get_all_registrations()
    found_students = [s for s in students if s.phone == phone]

    if not found_students:
        from keyboards.admin_kb import get_cancel_keyboard
        await message.answer(
            f"❌ Студент с телефоном {phone} не найден\n\n"
            "Попробуйте другой номер:",
            reply_markup=get_cancel_keyboard()
        )
        return

    student = found_students[0]
    status_text = config.STATUSES.get(student.status, student.status)

    info_text = (
        f"✅ *Студент найден!*\n\n"
        f"👤 Имя: {student.name}\n"
        f"📞 Телефон: {student.phone}\n"
        f"🎯 Курс: {student.course}\n"
        f"📊 Статус: {status_text}\n"
        f"🎓 Тип обучения: {student.training_type}\n"
        f"⏰ Расписание: {student.schedule}\n"
        f"💰 Цена: {student.price}\n"
        f"🆔 ID: {student.id}\n"
    )

    from keyboards.admin_kb import get_student_actions_keyboard
    await message.answer(
        info_text,
        parse_mode="Markdown",
        reply_markup=get_student_actions_keyboard(student.id, student.status, student.name)
    )
    await state.clear()


# ============ НАЗНАЧЕНИЕ ПРОБНОГО УРОКА ============

@router.callback_query(F.data.startswith("schedule_trial_"))
async def schedule_trial_start(callback: CallbackQuery, state: FSMContext):
    """Назначение пробного урока"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return

    try:
        reg_id = int(callback.data.replace("schedule_trial_", ""))
        student = db.get_student_by_id(reg_id)

        if not student:
            await callback.answer("❌ Студент не найден")
            return

        await state.set_state(AdminStates.waiting_for_trial_time)
        await state.update_data(reg_id=reg_id, student_name=student.name)

        from keyboards.admin_kb import get_cancel_keyboard
        await callback.message.edit_text(
            f"🎓 *Назначение пробного урока*\n\n"
            f"👤 Студент: *{student.name}*\n"
            f"📞 Телефон: {student.phone}\n"
            f"📚 Курс: {student.course}\n\n"
            f"⏰ Введите дату и время пробного урока\n"
            f"Формат: `2024-12-31 14:30:00`",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
    except ValueError:
        await callback.answer("❌ Ошибка: неверный ID")
    except Exception as e:
        logger.error(f"Error in schedule_trial_start: {e}")
        await callback.answer("❌ Произошла ошибка")

    await callback.answer()


@router.message(AdminStates.waiting_for_trial_time)
async def set_trial_time(message: Message, state: FSMContext):
    """Установка времени пробного урока"""
    if not is_admin(message.from_user.id):
        return

    if message.text in ["❌ Отмена", "◀️ Назад"]:
        await state.clear()
        from keyboards.admin_kb import get_admin_students_menu
        await message.answer(
            "❌ Отмена назначения пробного урока",
            reply_markup=get_admin_students_menu()
        )
        return

    # Валидация формата даты
    try:
        from datetime import datetime
        datetime.strptime(message.text, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        from keyboards.admin_kb import get_cancel_keyboard
        await message.answer(
            "❌ Неверный формат даты!\n"
            "Используйте: `2024-12-31 14:30:00`",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return

    data = await state.get_data()
    reg_id = data['reg_id']

    # Устанавливаем время и меняем статус на 'trial'
    success = db.set_trial_lesson_time(reg_id, message.text)

    if success:
        from keyboards.admin_kb import get_admin_students_menu
        await message.answer(
            f"✅ *Пробный урок назначен!*\n\n"
            f"👤 Студент: {data['student_name']}\n"
            f"⏰ Время: {message.text}\n"
            f"✅ Новый статус: *Пробный урок*",
            parse_mode="Markdown",
            reply_markup=get_admin_students_menu()
        )
        logger.info(f"✅ Пробный урок установлен для ID {reg_id} на {message.text}")
    else:
        from keyboards.admin_kb import get_admin_students_menu
        await message.answer(
            "❌ Ошибка при сохранении времени пробного урока",
            reply_markup=get_admin_students_menu()
        )

    await state.clear()