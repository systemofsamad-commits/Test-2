import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.student_states import StudentStates
from database import Database
from helpers import is_admin
from config import Config

logger = logging.getLogger(__name__)
router = Router(name="admin_progress_handlers")
config = Config()
db = Database(config.DB_NAME)


# Обновление прогресса
@router.callback_query(F.data.startswith("update_progress_"))
async def handle_update_progress(callback: CallbackQuery, state: FSMContext):
    """Обновление прогресса студента"""
    if not is_admin(callback.from_user.id):
        return

    registration_id = int(callback.data.split("_")[2])
    student = db.get_student_by_id(registration_id)

    if not student:
        await callback.answer("Студент не найден", show_alert=True)
        return

    await state.update_data(registration_id=registration_id)

    # Показываем меню выбора прогресса
    from keyboards.admin_kb import get_progress_update_keyboard
    await callback.message.edit_text(
        f"📊 Обновление прогресса для {student.name}\n"
        f"Текущий прогресс: {student.progress or 'Не указан'}",
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
        db.update_student_progress(registration_id, progress_text)

        student = db.get_student_by_id(registration_id)
        from keyboards.admin_kb import get_student_actions_keyboard
        await callback.message.edit_text(
            f"✅ Прогресс обновлен: {progress_text}\n"
            f"Для студента: {student.name}",
            reply_markup=get_student_actions_keyboard(
                registration_id,
                student.status,
                student.name
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

    db.update_student_progress(registration_id, message.text)

    student = db.get_student_by_id(registration_id)
    from keyboards.admin_kb import get_student_actions_keyboard
    await message.answer(
        f"✅ Прогресс обновлен: {message.text}\n"
        f"Для студента: {student.name}",
        reply_markup=get_student_actions_keyboard(
            registration_id,
            student.status,
            student.name
        )
    )
    await state.clear()


@router.callback_query(F.data.startswith("student_contacts_"))
async def handle_student_contacts(callback: CallbackQuery):
    """Показать контакты студента"""
    if not is_admin(callback.from_user.id):
        return

    registration_id = int(callback.data.split("_")[2])
    student = db.get_student_by_id(registration_id)

    if not student:
        await callback.answer("Студент не найден", show_alert=True)
        return

    contacts_text = f"""
📞 Контакты студента:

👤 Имя: {student.name}
📱 Телефон: {student.phone or 'Не указан'}
📧 Email: {getattr(student, 'email', 'Не указан')}
💬 Telegram: @{getattr(student, 'telegram', 'Не указан')}

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
    student = db.get_student_by_id(registration_id)

    if not student:
        await callback.answer("Студент не найден", show_alert=True)
        return

    full_info = f"""
📋 Полная информация о студенте:

👤 Основное:
- Имя: {student.name}
- ID: {registration_id}
- Статус: {config.STATUSES.get(student.status, student.status)}

📞 Контакты:
- Телефон: {student.phone or 'Не указан'}
- Email: {getattr(student, 'email', 'Не указан')}
- Telegram: @{getattr(student, 'telegram', 'Не указан')}

🎓 Обучение:
- Курс: {student.course}
- Группа: {getattr(student, 'group_name', 'Не назначена')}
- Прогресс: {student.progress or 'Не указан'}
- Преподаватель: {getattr(student, 'teacher_name', 'Не назначен')}

📅 Даты:
- Зарегистрирован: {getattr(student, 'registration_date', 'Не указана')}
- Последнее обновление: {getattr(student, 'last_update', 'Не указано')}
    """

    await callback.message.answer(full_info)
    await callback.answer()