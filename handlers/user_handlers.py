import asyncio
import datetime
import os
import sys

import aiogram.exceptions

# Добавляем путь к корневой папке проекта
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import logging

from states.user_states import RegistrationStates, FeedbackStates
from keyboards.user_kb import (
    get_main_keyboard,
    get_cancel_keyboard,
    get_confirmation_keyboard,
    get_courses_keyboard,
    get_training_types_keyboard,
    get_schedule_keyboard,
    get_cabinet_keyboard,
    get_materials_keyboard,
    get_quiz_keyboard,
    get_feedback_types_keyboard,
    get_rating_keyboard,
    get_feedback_confirmation_keyboard, get_progress_keyboard, get_quiz_results_keyboard
)
from utils.validators import validate_name, validate_phone, format_phone
from config import Config
from database import Database  # ✅ ДОБАВЛЕН ИМПОРТ!

user_router = Router(name="user_router")
config = Config()
db = Database(config.DB_NAME)
logger = logging.getLogger(__name__)


# Главное меню и информация
@user_router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "🎓 Добро пожаловать!",
        reply_markup=get_main_keyboard()
    )


@user_router.message(Command("help"))
async def help_command(message: Message):
    await message.answer("Помощь по боту...")


@user_router.callback_query(F.data == "new_registration")
async def start_new_registration(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(RegistrationStates.choosing_course)
    await callback.message.edit_text(
        "🎓 Выберите курс для записи:",
        reply_markup=get_courses_keyboard()
    )
    await callback.answer()


@user_router.callback_query(F.data == "about_center")
async def about_center(callback: CallbackQuery):
    about_text = (
        "🏫 *О нашем центре:*\n\n"
        "Мы предоставляем качественное образование по различным направлениям.\n\n"
        "📞 *Контакты:*\n"
        "Телефон: +7 (XXX) XXX-XX-XX\n"
        "Адрес: Ваш адрес\n\n"
        "🕒 *Часы работы:*\n"
        "Пн-Пт: 9:00-18:00\n"
        "Сб: 10:00-15:00\n"
        "Вс: выходной"
    )
    await callback.message.edit_text(
        about_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


# Процесс регистрации
@user_router.callback_query(F.data == "show_courses")
async def show_courses(callback: CallbackQuery):
    courses_text = "🎓 *Доступные курсы:*\n\n"
    for course, types_dict in config.COURSES.items():
        courses_text += f"*{course}:*\n"
        for training_type, price in types_dict.items():
            courses_text += f"  • {training_type}: {price}\n"
        courses_text += "\n"
    await callback.message.edit_text(courses_text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    await callback.answer()


@user_router.callback_query(F.data.startswith("course_"))
async def choose_course(callback: CallbackQuery, state: FSMContext):
    try:
        course_idx = int(callback.data.replace("course_", ""))
        courses_list = list(config.COURSES.keys())

        if 0 <= course_idx < len(courses_list):
            course = courses_list[course_idx]
            await state.update_data(course=course, course_idx=course_idx)
            await state.set_state(RegistrationStates.choosing_training_type)
            keyboard = get_training_types_keyboard(course_idx)
            await callback.message.edit_text("Выберите тип обучения:", reply_markup=keyboard)
    except ValueError as e:
        logger.error(f"Ошибка выбора курса: {e}")
        await callback.answer("Ошибка выбора курса")
    await callback.answer()


@user_router.callback_query(F.data.startswith("type_"))
async def choose_training_type(callback: CallbackQuery, state: FSMContext):
    try:
        data = callback.data.split("_")
        if len(data) >= 3:
            course_idx = int(data[1])
            type_idx = int(data[2])

            courses_list = list(config.COURSES.keys())
            if 0 <= course_idx < len(courses_list):
                course = courses_list[course_idx]
                training_types = list(config.COURSES[course].keys())

                if 0 <= type_idx < len(training_types):
                    training_type = training_types[type_idx]
                    price = config.COURSES[course][training_type]

                    await state.update_data(
                        training_type=training_type,
                        price=price,
                        course_idx=course_idx,
                        type_idx=type_idx
                    )
                    await state.set_state(RegistrationStates.choosing_schedule)
                    await callback.message.edit_text("Выберите расписание:", reply_markup=get_schedule_keyboard())
    except (ValueError, IndexError) as e:
        logger.error(f"Ошибка выбора типа обучения: {e}")
        await callback.answer("Ошибка выбора типа обучения")
    await callback.answer()


@user_router.callback_query(F.data.startswith("schedule_"))
async def choose_schedule(callback: CallbackQuery, state: FSMContext):
    try:
        schedule_idx = int(callback.data.replace("schedule_", ""))
        if 0 <= schedule_idx < len(config.SCHEDULES):
            schedule = config.SCHEDULES[schedule_idx]
            await state.update_data(schedule=schedule, schedule_idx=schedule_idx)
            await state.set_state(RegistrationStates.waiting_for_name)
            await callback.message.edit_text("Введите ваше имя и фамилию:", reply_markup=get_cancel_keyboard())
    except ValueError as e:
        logger.error(f"Ошибка выбора расписания: {e}")
        await callback.answer("Ошибка выбора расписания")
    await callback.answer()


@user_router.message(RegistrationStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_keyboard())
        return

    is_valid, error_msg = validate_name(message.text)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\nПожалуйста, введите имя еще раз:")
        return

    await state.update_data(name=message.text)
    await state.set_state(RegistrationStates.waiting_for_phone)
    await message.answer("Введите ваш номер телефона:", reply_markup=get_cancel_keyboard())


@user_router.message(RegistrationStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_keyboard())
        return

    is_valid, error_msg = validate_phone(message.text)
    if not is_valid:
        await message.answer(f"❌ {error_msg}\nПожалуйста, введите номер телефона еще раз:")
        return

    formatted_phone = format_phone(message.text)
    await state.update_data(phone=formatted_phone)
    data = await state.get_data()

    confirmation_text = (
        "✅ *Проверьте данные:*\n\n"
        f"👤 *Имя:* {data['name']}\n"
        f"📞 *Телефон:* `{formatted_phone}`\n"
        f"🎯 *Курс:* {data['course']}\n"
        f"📊 *Тип обучения:* {data['training_type']}\n"
        f"⏰ *Расписание:* {data['schedule']}\n"
        f"💰 *Стоимость:* {data['price']}\n\n"
        "Всё верно?"
    )
    await state.set_state(RegistrationStates.confirmation)
    await message.answer(confirmation_text, parse_mode="Markdown", reply_markup=get_confirmation_keyboard())


@user_router.callback_query(F.data == "confirm", RegistrationStates.confirmation)
async def confirm_registration(callback: CallbackQuery, state: FSMContext):
    """Регистрация студента с автоматическим переводом в статус 'active'"""
    data = await state.get_data()
    success = db.save_registration(
        user_id=callback.from_user.id,
        name=data['name'],
        phone=data['phone'],
        course=data['course'],
        training_type=data['training_type'],
        schedule=data['schedule'],
        price=data['price']
    )

    if success:
        # === НОВОЕ: АВТОМАТИЧЕСКИ УСТАНАВЛИВАЕМ СТАТУС 'ACTIVE' ===
        registrations = db.get_user_registrations(callback.from_user.id)
        if registrations:
            latest_reg = registrations[0]
            db.update_status(latest_reg.id, 'active')
            logger.info(f"✅ Студент {data['name']} (ID: {latest_reg.id}) зарегистрирован с статусом 'active'")

        await callback.message.edit_text(
            "🎉 *Запись успешно оформлена!*\n\n"
            "✅ Ваш статус: *Активный студент*\n"
            "⏳ Администратор свяжется с вами для консультации\n"
            "или назначения пробного урока.\n\n"
            "Вы можете отслеживать статус в разделе «👤 Мой кабинет».",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

        # === ОТПРАВКА УВЕДОМЛЕНИЯ АДМИНИСТРАТОРАМ ===
        try:
            message_text = (
                "📝 *НОВАЯ РЕГИСТРАЦИЯ СТУДЕНТА*\n\n"
                f"👤 *Имя:* {data['name']}\n"
                f"📞 *Телефон:* `{data['phone']}`\n"
                f"📚 *Курс:* {data['course']}\n"
                f"🎓 *Тип:* {data['training_type']}\n"
                f"⏰ *Расписание:* {data['schedule']}\n"
                f"💰 *Стоимость:* {data['price']}\n"
                f"✅ *Статус:* Активный студент\n"
                f"📍 *ID Пользователя:* {callback.from_user.id}\n\n"
                f"*Требуется:*\n"
                f"1. Позвонить для консультации\n"
                f"2. Назначить пробный урок\n"
                f"3. Перевести в статус 'Пробный урок'"
            )

            if hasattr(config, 'CHANNEL_ID') and config.CHANNEL_ID:
                await callback.bot.send_message(config.CHANNEL_ID, message_text, parse_mode="Markdown")
                logger.info(f"✅ Уведомление отправлено в канал {config.CHANNEL_ID}")

        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомления: {e}")

    else:
        await callback.message.edit_text(
            "❌ Произошла ошибка при сохранении запи. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_keyboard()
        )

    await state.clear()

# Функционал кабинета
@user_router.callback_query(F.data == "show_cabinet")
async def show_cabinet(callback: CallbackQuery):
    registrations = db.get_user_registrations(callback.from_user.id)
    if not registrations:
        await callback.message.edit_text(
            "У вас пока нет активных записей.\n\nХотите записаться на курс? Нажмите «📝 Новая запись»!",
            reply_markup=get_main_keyboard()
        )
        return

    for reg in registrations:
        cabinet_text = (
            f"📋 *Ваша запись #{reg.id}:*\n\n"
            f"🎯 *Курс:* {reg.course}\n"
            f"📊 *Тип:* {reg.training_type}\n"
            f"⏰ *Расписание:* {reg.schedule}\n"
            f"💰 *Стоимость:* {reg.price}\n"
            f"📅 *Дата записи:* {reg.created_at}\n"
        )
        await callback.message.answer(cabinet_text, parse_mode="Markdown")

    await callback.message.answer("Дополнительные функции:", reply_markup=get_cabinet_keyboard(has_registrations=True))
    await callback.answer()


@user_router.callback_query(F.data == "show_materials")
async def show_materials(callback: CallbackQuery):
    registrations = db.get_user_registrations(callback.from_user.id)

    if not registrations:
        await callback.message.edit_text("У вас нет активных курсов.", reply_markup=get_main_keyboard())
        return

    course = registrations[0].course
    await callback.message.edit_text(
        f"📚 Материалы по курсу {course}:",
        reply_markup=get_materials_keyboard(course)
    )
    await callback.answer()

@user_router.callback_query(F.data == "add_reminder")
async def add_reminder_start(callback: CallbackQuery):
    """Начало добавления напоминания"""
    await callback.message.edit_text(
        "⏰ *Добавление напоминания*\n\n"
        "Введите текст напоминания:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )

@user_router.callback_query(F.data == "show_reminders")
async def show_reminders(callback: CallbackQuery):
    """Показать напоминания пользователя"""
    reminders = db.get_user_reminders(callback.from_user.id)

    if not reminders:
        await callback.message.edit_text(
            "📋 У вас пока нет напоминаний.\n\n"
            "Хотите добавить напоминание?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить напоминание", callback_data="add_reminder")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="show_cabinet")]
            ])
        )
        return

    reminders_text = "⏰ *Ваши напоминания:*\n\n"

    for i, reminder in enumerate(reminders, 1):
        status = "✅ Отправлено" if reminder['sent'] else "⏳ Ожидает"
        reminders_text += (
            f"{i}. {reminder['text']}\n"
            f"   📅 {reminder['due_date']}\n"
            f"   {status}\n\n"
        )

    await callback.message.edit_text(
        reminders_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить напоминание", callback_data="add_reminder")],
            [InlineKeyboardButton(text="🔙 В кабинет", callback_data="show_cabinet")]
        ])
    )
    await callback.answer()


@user_router.callback_query(F.data == "show_progress")
async def show_progress(callback: CallbackQuery):
    """Показать прогресс обучения"""
    registrations = db.get_user_registrations(callback.from_user.id)

    if not registrations:
        await callback.message.edit_text(
            "У вас пока нет активных записей для отслеживания прогресса.",
            reply_markup=get_main_keyboard()
        )
        return

    progress_text = "📊 *Ваш прогресс:*\n\n"

    for reg in registrations:
        progress_value = getattr(reg, 'progress', 0.0) or 0.0
        attendance_value = getattr(reg, 'attendance', 0) or 0
        grade_value = getattr(reg, 'grade', 'Нет оценки')

        progress_text += (
            f"📚 *{reg.course}*\n"
            f"📈 Прогресс: {progress_value:.1f}%\n"
            f"📅 Посещаемость: {attendance_value} занятий\n"
        )

        if grade_value and grade_value != 'Нет оценки':
            progress_text += f"⭐ Оценка: {grade_value}\n"

        progress_text += "\n"

    await callback.message.edit_text(
        progress_text,
        parse_mode="Markdown",
        reply_markup=get_progress_keyboard()
    )
    await callback.answer()


@user_router.callback_query(F.data == "start_quiz")
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    """Начать тест/викторину"""
    registrations = db.get_user_registrations(callback.from_user.id)

    if not registrations:
        await callback.message.edit_text(
            "❌ У вас нет активных курсов для прохождения теста.",
            reply_markup=get_main_keyboard()
        )
        return

    course = registrations[0].course

    if course not in config.QUIZZES:
        await callback.message.edit_text(
            f"❌ Для курса '{course}' пока нет доступных тестов.",
            reply_markup=get_cabinet_keyboard(has_registrations=True)
        )
        return

    # Начинаем тест с первого вопроса
    await state.update_data(
        quiz_course=course,
        quiz_index=0,
        quiz_correct=0,
        quiz_total=len(config.QUIZZES[course])
    )

    await show_quiz_question(callback.message, state, 0, course)
    await callback.answer()


async def show_quiz_question(message, state: FSMContext, question_index: int, course: str):
    """Показать вопрос теста"""
    questions = config.QUIZZES[course]

    if question_index >= len(questions):
        # Тест завершен
        data = await state.get_data()
        correct = data.get('quiz_correct', 0)
        total = data.get('quiz_total', 0)
        percentage = (correct / total * 100) if total > 0 else 0

        result_text = (
            f"🎉 *Тест завершен!*\n\n"
            f"✅ Правильных ответов: {correct} из {total}\n"
            f"📊 Результат: {percentage:.1f}%\n\n"
        )

        if percentage >= 80:
            result_text += "🌟 Отличный результат!"
        elif percentage >= 60:
            result_text += "👍 Хороший результат!"
        else:
            result_text += "📚 Рекомендуем повторить материал"

        await message.edit_text(
            result_text,
            parse_mode="Markdown",
            reply_markup=get_quiz_results_keyboard()
        )
        await state.clear()
        return

    question = questions[question_index]

    question_text = (
        f"❓ *Вопрос {question_index + 1} из {len(questions)}*\n\n"
        f"{question['question']}"
    )

    await message.edit_text(
        question_text,
        parse_mode="Markdown",
        reply_markup=get_quiz_keyboard(question_index, question['options'])
    )


@user_router.callback_query(F.data.startswith("quiz_"))
async def handle_quiz_answer(callback: CallbackQuery, state: FSMContext):
    """Обработка ответа на вопрос теста"""

    if callback.data == "cancel_quiz":
        await state.clear()
        await callback.message.edit_text(
            "❌ Тест прерван.",
            reply_markup=get_cabinet_keyboard(has_registrations=True)
        )
        await callback.answer()
        return

    try:
        parts = callback.data.split("_")
        question_index = int(parts[1])
        answer_index = int(parts[2])

        data = await state.get_data()
        course = data['quiz_course']
        correct_count = data.get('quiz_correct', 0)

        questions = config.QUIZZES[course]
        question = questions[question_index]

        is_correct = (answer_index == question['answer'])

        if is_correct:
            correct_count += 1
            await state.update_data(quiz_correct=correct_count)
            result_emoji = "✅"
            result_text = "Правильно!"
        else:
            result_emoji = "❌"
            result_text = f"Неправильно. Правильный ответ: {question['options'][question['answer']]}"

        explanation_text = (
            f"{result_emoji} *{result_text}*\n\n"
            f"💡 {question['explanation']}"
        )

        await callback.answer(result_text, show_alert=True)

        # Переход к следующему вопросу
        next_index = question_index + 1

        await callback.message.edit_text(explanation_text, parse_mode="Markdown")
        await asyncio.sleep(2)

        await show_quiz_question(callback.message, state, next_index, course)

    except Exception as e:
        logger.error(f"Error in quiz handler: {e}")
        await callback.answer("❌ Ошибка обработки ответа")

# Обратная связь
@user_router.callback_query(F.data == "give_feedback")
async def start_feedback(callback: CallbackQuery, state: FSMContext):
    """Начало процесса обратной связи"""
    registrations = db.get_user_registrations(callback.from_user.id)

    if not registrations:
        await callback.message.edit_text(
            "У вас пока нет активных записей для оставления отзыва.",
            reply_markup=get_main_keyboard()
        )
        return

    await state.set_state(FeedbackStates.waiting_for_feedback_text)
    await state.update_data(
        user_id=callback.from_user.id,
        user_name=callback.from_user.full_name,
        registrations=registrations
    )

    await callback.message.edit_text(
        "📝 *Обратная связь*\n\n"
        "Пожалуйста, выберите тип обращения:",
        parse_mode="Markdown",
        reply_markup=get_feedback_types_keyboard()
    )
    await callback.answer()


@user_router.callback_query(F.data.startswith("feedback_type_"))
async def choose_feedback_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа обратной связи"""
    feedback_type = callback.data.replace("feedback_type_", "")
    logger.debug(f"Feedback type received: {feedback_type}")

    type_names = {
        "review": "отзыв",
        "suggestion": "предложение по улучшению",
        "issue": "сообщение о проблеме"
    }

    if feedback_type not in type_names:
        await callback.message.edit_text(
            "❌ Неверный тип обратной связи. Пожалуйста, выберите снова.",
            reply_markup=get_feedback_types_keyboard()
        )
        await callback.answer()
        return

    await state.update_data(feedback_type=feedback_type)

    if feedback_type == "review":
        await state.set_state(FeedbackStates.waiting_for_rating)
        await callback.message.edit_text(
            "⭐ *Оцените наш образовательный центр*\n\n"
            "Пожалуйста, выберите оценку от 1 до 5 звезд:",
            parse_mode="Markdown",
            reply_markup=get_rating_keyboard()
        )
    else:
        await state.set_state(FeedbackStates.waiting_for_feedback_text)
        prompt_text = {
            "suggestion": "💡 *Предложение по улучшению*\n\nПожалуйста, напишите ваше предложение:",
            "issue": "🐞 *Сообщение о проблеме*\n\nОпишите, пожалуйста, возникшую проблему:"
        }
        await callback.message.edit_text(
            prompt_text[feedback_type],
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
    await callback.answer()


@user_router.callback_query(F.data.startswith("rating_"), FeedbackStates.waiting_for_rating)
async def get_rating(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора оценки"""
    rating = int(callback.data.replace("rating_", ""))
    await state.update_data(rating=rating)
    await state.set_state(FeedbackStates.waiting_for_feedback_text)

    await callback.message.edit_text(
        "📝 *Напишите ваш отзыв*\n\n"
        f"Вы выбрали оценку: {rating}⭐\n"
        "Теперь напишите ваш отзыв о нашем образовательном центре:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@user_router.message(FeedbackStates.waiting_for_feedback_text)
async def get_feedback_text(message: Message, state: FSMContext):
    """Обработка текста обратной связи"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_keyboard())
        return

    data = await state.get_data()
    feedback_text = message.text

    await state.update_data(feedback_text=feedback_text)

    type_names = {
        "review": "Отзыв",
        "suggestion": "Предложение по улучшению",
        "issue": "Сообщение о проблеме"
    }

    confirmation_text = f"📋 *Проверьте ваше обращение:*\n\n"
    confirmation_text += f"📝 *Тип:* {type_names[data['feedback_type']]}\n"

    if data['feedback_type'] == 'review':
        confirmation_text += f"⭐ *Оценка:* {data['rating']}/5\n"

    confirmation_text += f"📄 *Текст:*\n{feedback_text}\n\n"
    confirmation_text += "Всё верно?"

    await message.answer(
        confirmation_text,
        parse_mode="Markdown",
        reply_markup=get_feedback_confirmation_keyboard()
    )


@user_router.callback_query(F.data == "feedback_send")
async def send_feedback(callback: CallbackQuery, state: FSMContext):
    """Отправка обратной связи"""
    data = await state.get_data()

    success = db.save_feedback(
        user_id=data['user_id'],
        user_name=data['user_name'],
        feedback_type=data['feedback_type'],
        feedback_text=data['feedback_text'],
        rating=data.get('rating', None),
        created_at=datetime.datetime.now()
    )

    if success:
        await send_feedback_to_admins(callback.bot, data)

        await callback.message.edit_text(
            "✅ *Спасибо за вашу обратную связь!*\n\n"
            "Мы ценим ваше мнение и обязательно рассмотрим ваше обращение.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        await callback.message.edit_text(
            "❌ *Произошла ошибка при отправке отзыва.*\n\n"
            "Пожалуйста, попробуйте позже.",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

    await state.clear()
    await callback.answer()


@user_router.callback_query(F.data.in_(["feedback_review", "feedback_suggestion", "feedback_issue"]))
async def handle_feedback_type_selection(callback: CallbackQuery, state: FSMContext):
    feedback_types = {
        "feedback_review": "review",
        "feedback_suggestion": "suggestion",
        "feedback_issue": "issue"
    }

    feedback_type = feedback_types[callback.data]
    await state.update_data(feedback_type=feedback_type)

    if feedback_type == "review":
        await state.set_state(FeedbackStates.waiting_for_rating)
        await callback.message.edit_text(
            "⭐ Оцените наш центр (1-5 звезд):",
            reply_markup=get_rating_keyboard()
        )
    else:
        await state.set_state(FeedbackStates.waiting_for_feedback_text)
        prompt = "💡 Опишите ваше предложение:" if feedback_type == "suggestion" else "🐞 Опишите проблему:"
        await callback.message.edit_text(prompt, reply_markup=get_cancel_keyboard())

@user_router.callback_query(F.data == "feedback_edit")
async def edit_feedback(callback: CallbackQuery, state: FSMContext):
    """Редактирование обратной связи"""
    await state.set_state(FeedbackStates.waiting_for_feedback_text)

    await callback.message.edit_text(
        "📝 *Исправьте ваш текст:*\n\n"
        "Пожалуйста, напишите исправленный вариант:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


async def send_feedback_to_admins(bot, feedback_data):
    """Отправка уведомления о новой обратной связи администраторам"""
    try:
        type_names = {
            "review": "📝 НОВЫЙ ОТЗЫВ",
            "suggestion": "💡 НОВОЕ ПРЕДЛОЖЕНИЕ",
            "issue": "🐞 СООБЩЕНИЕ О ПРОБЛЕМЕ"
        }

        message_text = (
            f"{type_names[feedback_data['feedback_type']]}\n\n"
            f"👤 *Пользователь:* {feedback_data['user_name']}\n"
            f"🆔 *ID:* {feedback_data['user_id']}\n"
        )

        if feedback_data['feedback_type'] == 'review':
            message_text += f"⭐ *Оценка:* {feedback_data['rating']}/5\n"

        message_text += f"📄 *Текст:*\n{feedback_data['feedback_text']}\n\n"
        message_text += f"🕒 *Время:* {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"

        for admin_id in config.ADMIN_IDS:
            try:
                await bot.send_message(admin_id, message_text, parse_mode="Markdown")
            except aiogram.exceptions.TelegramBadRequest as e:
                logger.error(f"❌ Ошибка отправки администратору {admin_id}: {e}")
            except aiogram.exceptions.TelegramForbiddenError as e:
                logger.warning(f"❌ Бот заблокирован администратором {admin_id}: {e}")
            except Exception as e:
                logger.error(f"❌ Неожиданная ошибка при отправке администратору {admin_id}: {e}")

    except KeyError as e:
        logger.error(f"❌ Ошибка в данных обратной связи: {e}")
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при отправке уведомления: {e}")


# Общие обработчики
@user_router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Отменено.", reply_markup=get_main_keyboard())
    await callback.answer()


@user_router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню с обработкой ошибок редактирования"""
    await state.clear()

    try:
        await callback.message.edit_text(
            "Добро пожаловать в главное меню!",
            reply_markup=get_main_keyboard()
        )
    except aiogram.exceptions.TelegramBadRequest:
        await callback.message.answer(
            "Добро пожаловать в главное меню!",
            reply_markup=get_main_keyboard()
        )

    await callback.answer()


def register_user_handlers(dp):
    dp.include_router()