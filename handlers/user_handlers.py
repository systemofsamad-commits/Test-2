import asyncio
import datetime
import logging
import os
import sys

import aiogram.exceptions

from database import registrations

# Добавляем путь к корневой папке проекта
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from states.user_states import RegistrationStates, FeedbackStates
# noinspection PyProtectedMember
from keyboards.user_kb import (
    get_main_keyboard,
    get_cancel_keyboard,
    get_confirmation_keyboard,
    get_courses_keyboard,
    get_training_types_keyboard,
    get_schedule_keyboard,
    get_cabinet_keyboard,
    get_materials_keyboard,
    get_feedback_types_keyboard,
    get_rating_keyboard,
    get_feedback_confirmation_keyboard,
    get_progress_keyboard,
    get_quiz_results_keyboard,
    get_registrations_keyboard,
    get_registration_detail_keyboard,
    get_back_keyboard, get_quiz_question_keyboard
)
from utils.validators import validate_name, validate_phone, format_phone
from config import Config
from helpers import get_db

user_router = Router(name="user_router")
config = Config()
db = get_db()
logger = logging.getLogger(__name__)


# Главное меню и информация
@user_router.message(Command("start"))
async def start_command(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        "🎓 Добро пожаловать в образовательный центр!\n\n"
        "Выберите действие:",
        reply_markup=get_main_keyboard()
    )


@user_router.message(Command("help"))
async def help_command(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "📖 *Помощь по боту:*\n\n"
        "🎓 *Основные функции:*\n"
        "• 📝 Новая запись - записаться на курс\n"
        "• 👤 Мой кабинет - личный кабинет\n"
        "• 📚 Курсы - список доступных курсов\n"
        "• ℹ️ О центре - информация о нас\n"
        "• 💬 Отзыв - оставить отзыв\n\n"
        "📞 *Поддержка:*\n"
        "Если возникли вопросы, свяжитесь с нами!",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )


@user_router.callback_query(F.data == "new_registration")
async def start_new_registration(callback: CallbackQuery, state: FSMContext):
    """Начать новую регистрацию на курс"""
    await state.clear()
    await state.set_state(RegistrationStates.choosing_course)

    await callback.message.edit_text(
        "🎓 *Запись на курс*\n\nВыберите курс:",
        parse_mode="Markdown",
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
    """Показать список курсов"""
    courses_text = "🎓 *Доступные курсы:*\n\n"

    for course, types_dict in config.COURSES.items():
        courses_text += f"*{course}:*\n"
        for training_type, price in types_dict.items():
            courses_text += f"  • {training_type}: {price}\n"
        courses_text += "\n"
        await callback.message.edit_text(
            courses_text,
            parse_mode="Markdown",
            reply_markup=get_back_keyboard("back_to_main")
        )
    await callback.answer()


@user_router.callback_query(F.data.startswith("course_"), RegistrationStates.choosing_course)
async def choose_course(callback: CallbackQuery, state: FSMContext):
    """Выбор курса"""
    try:
        course_idx = int(callback.data.replace("course_", ""))
        courses_list = list(config.COURSES.keys())

        if 0 <= course_idx < len(courses_list):
            course = courses_list[course_idx]
            await state.update_data(course=course, course_idx=course_idx)
            await state.set_state(RegistrationStates.choosing_training_type)

            await callback.message.edit_text(
                f"🎓 *Курс: {course}*\n\nВыберите тип обучения:",
                parse_mode="Markdown",
                reply_markup=get_training_types_keyboard(course_idx)
            )
        else:
            await callback.answer("❌ Неверный курс", show_alert=True)

    except ValueError as e:
        logger.error(f"Ошибка выбора курса: {e}")
        await callback.answer("❌ Ошибка выбора курса", show_alert=True)

    await callback.answer()


@user_router.callback_query(F.data.startswith("type_"), RegistrationStates.choosing_training_type)
async def choose_training_type(callback: CallbackQuery, state: FSMContext):
    """Выбор типа обучения"""
    try:
        data_parts = callback.data.split("_")
        if len(data_parts) >= 3:
            course_idx = int(data_parts[1])
            type_idx = int(data_parts[2])

            courses_list = list(config.COURSES.keys())
            if 0 <= course_idx < len(courses_list):
                course = courses_list[course_idx]
                training_types = list(config.COURSES[course].keys())

                if 0 <= type_idx < len(training_types):
                    training_type = training_types[type_idx]
                    price = config.COURSES[course][training_type]

                    await state.update_data(
                        training_type=training_type,
                        price=price
                    )
                    await state.set_state(RegistrationStates.choosing_schedule)

                    await callback.message.edit_text(
                        f"📊 *Тип обучения: {training_type}*\n"
                        f"💰 *Стоимость: {price}*\n\n"
                        "Выберите расписание:",
                        parse_mode="Markdown",
                        reply_markup=get_schedule_keyboard()
                    )

    except (ValueError, IndexError) as e:
        logger.error(f"Ошибка выбора типа обучения: {e}")
        await callback.answer("❌ Ошибка выбора типа обучения", show_alert=True)

    await callback.answer()


@user_router.callback_query(F.data.startswith("schedule_"), RegistrationStates.choosing_schedule)
async def choose_schedule(callback: CallbackQuery, state: FSMContext):
    """Выбор расписания"""
    try:
        schedule_idx = int(callback.data.replace("schedule_", ""))

        if 0 <= schedule_idx < len(config.SCHEDULES):
            schedule = config.SCHEDULES[schedule_idx]
            await state.update_data(schedule=schedule)
            await state.set_state(RegistrationStates.waiting_for_name)

            await callback.message.edit_text(
                "👤 *Введите ваше имя и фамилию:*\n\n"
                "Например: Иван Иванов",
                parse_mode="Markdown",
                reply_markup=get_cancel_keyboard()
            )
        else:
            await callback.answer("❌ Неверное расписание", show_alert=True)

    except ValueError as e:
        logger.error(f"Ошибка выбора расписания: {e}")
        await callback.answer("❌ Ошибка выбора расписания", show_alert=True)

    await callback.answer()


@user_router.message(RegistrationStates.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    """Получение имени"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_keyboard())
        return

    is_valid, error_msg = validate_name(message.text)
    if not is_valid:
        await message.answer(
            f"❌ {error_msg}\n\nПожалуйста, введите имя еще раз:",
            reply_markup=get_cancel_keyboard()
        )
        return

    await state.update_data(name=message.text)
    await state.set_state(RegistrationStates.waiting_for_phone)

    await message.answer(
        "📞 *Введите ваш номер телефона:*\n\n"
        "Например: +998901234567",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )


@user_router.message(RegistrationStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext):
    """Получение телефона"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_keyboard())
        return

    is_valid, error_msg = validate_phone(message.text)
    if not is_valid:
        await message.answer(
            f"❌ {error_msg}\n\nПожалуйста, введите номер телефона еще раз:",
            reply_markup=get_cancel_keyboard()
        )
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
    await message.answer(
        confirmation_text,
        parse_mode="Markdown",
        reply_markup=get_confirmation_keyboard()
    )


@user_router.callback_query(F.data == "confirm_registration", RegistrationStates.confirmation)
async def confirm_registration(callback: CallbackQuery, state: FSMContext):
    """Подтверждение регистрации с детальным логированием"""
    try:
        data = await state.get_data()

        print("\n" + "=" * 70)
        print(f"🔍 DEBUG: Starting registration confirmation")
        print(f"👤 User ID: {callback.from_user.id}")
        print(f"📝 Username: @{callback.from_user.username or 'N/A'}")
        print(f"📋 Registration data: {data}")
        print("=" * 70)

        # ============================================
        # ШАГ 1: Создание пользователя
        # ============================================
        print("\n📌 ШАГ 1: Создание пользователя...")
        user_query = """
                     INSERT OR IGNORE
                     INTO users (telegram_id, full_name, phone)
                     VALUES (?, ?, ?)
                     """
        rows_affected = db.execute_update(user_query, (
            callback.from_user.id,
            data['name'],
            data['phone']
        ))
        print(f"✅ User query executed: {rows_affected} rows affected")

        # Получаем user_id
        user_query = "SELECT id FROM users WHERE telegram_id = ?"
        user_rows = db.execute_query(user_query, (callback.from_user.id,))
        user_id = user_rows[0]['id'] if user_rows else None

        if not user_id:
            print("❌ ERROR: Failed to create/get user!")
            await callback.message.edit_text("❌ Ошибка создания пользователя")
            await callback.answer()
            return

        print(f"✅ User ID получен: {user_id}")

        # ============================================
        # ШАГ 2: Получение ID курса, типа обучения и расписания
        # ============================================
        print("\n📌 ШАГ 2: Получение ID справочников...")

        # Получаем ID курса по названию
        course_query = "SELECT id FROM courses WHERE name = ?"
        course_rows = db.execute_query(course_query, (data['course'],))
        course_id = course_rows[0]['id'] if course_rows else None
        print(f"  📚 Course ID: {course_id} (Курс: {data['course']})")

        # Получаем ID типа обучения
        training_query = "SELECT id FROM training_types WHERE name = ?"
        training_rows = db.execute_query(training_query, (data['training_type'],))
        training_type_id = training_rows[0]['id'] if training_rows else None
        print(f"  📊 Training Type ID: {training_type_id} (Тип: {data['training_type']})")

        # Получаем ID расписания
        schedule_query = "SELECT id FROM schedules WHERE name = ?"
        schedule_rows = db.execute_query(schedule_query, (data['schedule'],))
        schedule_id = schedule_rows[0]['id'] if schedule_rows else None
        print(f"  ⏰ Schedule ID: {schedule_id} (Расписание: {data['schedule']})")

        if not course_id or not training_type_id or not schedule_id:
            print(f"❌ ERROR: Missing IDs - Course: {course_id}, Training: {training_type_id}, Schedule: {schedule_id}")
            await callback.message.edit_text("❌ Ошибка: не найдены данные курса")
            await callback.answer()
            return

        # ============================================
        # ШАГ 3: Создание регистрации
        # ============================================
        print("\n📌 ШАГ 3: Создание регистрации в БД...")
        print(f"  Параметры:")
        print(f"    - user_id: {user_id}")
        print(f"    - course_id: {course_id}")
        print(f"    - training_type_id: {training_type_id}")
        print(f"    - schedule_id: {schedule_id}")
        print(f"    - status: 'trial'")

        # ✅ ИСПРАВЛЕНО: Используем прямой SQL INSERT вместо метода репозитория
        insert_query = """
                       INSERT INTO registrations
                       (user_id, full_name, phone, course_id, training_type_id, schedule_id, status_code, created_at, \
                        updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now')) \
                       """

        reg_id = db.execute_insert(insert_query, (
            user_id,
            data['name'],
            data['phone'],
            course_id,
            training_type_id,
            schedule_id,
            'trial'
        ))

        print(f"✅ ✅ ✅ РЕГИСТРАЦИЯ СОЗДАНА! ID: {reg_id} ✅ ✅ ✅")
        print(f"📊 БД: Запись #{reg_id} сохранена в таблицу 'registrations'")
        logger.info(f"✅ Registration #{reg_id} created for user {callback.from_user.id}")

        # ============================================
        # ШАГ 4: Подтверждение пользователю
        # ============================================
        print("\n📌 ШАГ 4: Отправка подтверждения пользователю...")
        success_message = (
            "✅ *Регистрация успешно завершена!*\n\n"
            f"👤 *Имя:* {data['name']}\n"
            f"📞 *Телефон:* {data['phone']}\n\n"
            f"🎓 *Курс:* {data['course']}\n"
            f"📊 *Тип обучения:* {data['training_type']}\n"
            f"⏰ *Расписание:* {data['schedule']}\n"
            f"💰 *Стоимость:* {data['price']}\n\n"
            f"🔢 *Номер заявки:* #{reg_id}\n\n"
            "📝 *Ваша заявка отправлена!*\n"
            "Наш администратор свяжется с вами в ближайшее время.\n\n"
            "Спасибо за обращение! 🙏"
        )

        await callback.message.edit_text(
            success_message,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        print("✅ Подтверждение отправлено пользователю")

        # ============================================
        # ШАГ 5: Уведомление администраторам
        # ============================================
        print("\n📌 ШАГ 5: Отправка уведомлений администраторам...")
        print(f"  Список администраторов: {config.ADMIN_IDS}")

        bot = callback.bot
        await send_registration_to_admins(bot, data, callback.from_user, reg_id)

        # ============================================
        # ШАГ 6: Отправка в канал (если настроен)
        # ============================================
        if hasattr(config, 'CHANNEL_ID') and config.CHANNEL_ID:
            print(f"\n📌 ШАГ 6: Отправка уведомления в канал {config.CHANNEL_ID}...")
            try:
                channel_message = (
                    f"🆕 *НОВАЯ РЕГИСТРАЦИЯ #{reg_id}*\n\n"
                    f"👤 *Студент:* {data['name']}\n"
                    f"🎓 *Курс:* {data['course']}\n"
                    f"📊 *Тип:* {data['training_type']}\n"
                    f"⏰ *Расписание:* {data['schedule']}\n"
                    f"💰 *Стоимость:* {data['price']}\n\n"
                    f"🕒 {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
                await bot.send_message(config.CHANNEL_ID, channel_message, parse_mode="Markdown")
                print(f"✅ Уведомление отправлено в канал {config.CHANNEL_ID}")
                logger.info(f"✅ Registration #{reg_id} notification sent to channel {config.CHANNEL_ID}")
            except Exception as e:
                print(f"❌ Ошибка отправки в канал: {e}")
                logger.error(f"❌ Error sending to channel: {e}", exc_info=True)
        else:
            print(f"\n📌 ШАГ 6: Канал не настроен, пропускаем")

        # ============================================
        # ШАГ 7: Очистка состояния
        # ============================================
        print("\n📌 ШАГ 7: Очистка состояния FSM...")
        await state.clear()
        await callback.answer("✅ Регистрация завершена!")
        print("✅ Состояние очищено")

        print("\n" + "=" * 70)
        print(f"🎉 РЕГИСТРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
        print(f"📊 ID регистрации: {reg_id}")
        print(f"👤 Пользователь: {data['name']} (ID: {user_id})")
        print(f"🎓 Курс: {data['course']}")
        print("=" * 70 + "\n")

        logger.info(f"✅ User {callback.from_user.id} registered successfully with registration ID: {reg_id}")

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ ❌ ❌ ОШИБКА В ПРОЦЕССЕ РЕГИСТРАЦИИ!")
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Сообщение: {str(e)}")
        print("=" * 70 + "\n")

        logger.error(f"❌ Error in confirm_registration: {e}", exc_info=True)

        await callback.message.edit_text(
            "❌ Произошла ошибка при сохранении. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        await callback.answer("❌ Ошибка регистрации")


async def send_registration_to_admins(bot, data, user, reg_id):
    """Отправка уведомления о новой регистрации администраторам"""
    try:
        message_text = (
            f"🆕 *НОВАЯ РЕГИСТРАЦИЯ #{reg_id}*\n\n"
            f"👤 *Имя:* {data['name']}\n"
            f"📞 *Телефон:* {data['phone']}\n"
            f"🆔 *Telegram ID:* `{user.id}`\n"
            f"📝 *Username:* @{user.username or 'не указан'}\n\n"
            f"🎓 *Курс:* {data['course']}\n"
            f"📊 *Тип обучения:* {data['training_type']}\n"
            f"⏰ *Расписание:* {data['schedule']}\n"
            f"💰 *Стоимость:* {data['price']}\n\n"
            f"🕒 *Время:* {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        sent_count = 0
        failed_count = 0

        for admin_id in config.ADMIN_IDS:
            try:
                print(f"  📤 Отправка администратору {admin_id}...")
                await bot.send_message(admin_id, message_text, parse_mode="Markdown")
                sent_count += 1
                print(f"  ✅ Уведомление отправлено админу {admin_id}")
                logger.info(f"✅ Notification sent to admin {admin_id}")
            except aiogram.exceptions.TelegramForbiddenError:
                failed_count += 1
                print(f"  ❌ Админ {admin_id} заблокировал бота")
                logger.error(f"❌ Admin {admin_id} blocked the bot")
            except Exception as e:
                failed_count += 1
                print(f"  ❌ Ошибка отправки админу {admin_id}: {e}")
                logger.error(f"❌ Error sending to admin {admin_id}: {e}")

        print(f"\n📊 Статистика отправки администраторам:")
        print(f"  ✅ Успешно: {sent_count}/{len(config.ADMIN_IDS)}")
        print(f"  ❌ Ошибок: {failed_count}/{len(config.ADMIN_IDS)}")

        logger.info(f"✅ Registration notification sent to {sent_count}/{len(config.ADMIN_IDS)} admins")

    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА в send_registration_to_admins: {e}")
        logger.error(f"❌ Critical error in send_registration_to_admins: {e}", exc_info=True)


@user_router.callback_query(F.data == "leave_feedback")
async def show_feedback_menu(callback: CallbackQuery, state: FSMContext):
    """Показать меню обратной связи"""
    await state.clear()

    # Сохраняем информацию о пользователе
    await state.update_data(
        user_id=callback.from_user.id,
        user_name=callback.from_user.full_name or callback.from_user.username or "Пользователь"
    )

    await callback.message.edit_text(
        "💬 *Обратная связь*\n\n"
        "Выберите тип обращения:",
        parse_mode="Markdown",
        reply_markup=get_feedback_types_keyboard()
    )
    await callback.answer()


@user_router.callback_query(F.data.in_(["feedback_review", "feedback_suggestion", "feedback_issue"]))
async def handle_feedback_type(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа обратной связи"""
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
            "⭐ *Оцените наш образовательный центр*\n\n"
            "Выберите оценку от 1 до 5 звезд:",
            parse_mode="Markdown",
            reply_markup=get_rating_keyboard()
        )
    else:
        await state.set_state(FeedbackStates.waiting_for_feedback_text)
        prompts = {
            "suggestion": "💡 *Предложение по улучшению*\n\nНапишите ваше предложение:",
            "issue": "🐞 *Сообщение о проблеме*\n\nОпишите возникшую проблему:"
        }
        await callback.message.edit_text(
            prompts[feedback_type],
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )

    await callback.answer()


@user_router.callback_query(F.data.startswith("rating_"), FeedbackStates.waiting_for_rating)
async def get_rating(callback: CallbackQuery, state: FSMContext):
    """Получение оценки"""
    rating = int(callback.data.replace("rating_", ""))
    await state.update_data(rating=rating)
    await state.set_state(FeedbackStates.waiting_for_feedback_text)

    await callback.message.edit_text(
        f"📝 *Напишите ваш отзыв*\n\n"
        f"Вы выбрали оценку: {'⭐' * rating}\n\n"
        "Теперь напишите ваш отзыв о центре:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@user_router.message(FeedbackStates.waiting_for_feedback_text)
async def get_feedback_text(message: Message, state: FSMContext):
    """Получение текста обратной связи"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_keyboard())
        return

    data = await state.get_data()
    await state.update_data(feedback_text=message.text)

    type_names = {
        "review": "Отзыв",
        "suggestion": "Предложение",
        "issue": "Сообщение о проблеме"
    }

    confirmation_text = "📋 *Проверьте ваше обращение:*\n\n"
    confirmation_text += f"📝 *Тип:* {type_names[data['feedback_type']]}\n"

    if data['feedback_type'] == 'review':
        confirmation_text += f"⭐ *Оценка:* {data['rating']}/5\n"

    confirmation_text += f"📄 *Текст:*\n{message.text}\n\nВсё верно?"

    await message.answer(
        confirmation_text,
        parse_mode="Markdown",
        reply_markup=get_feedback_confirmation_keyboard()
    )


@user_router.callback_query(F.data == "feedback_send")
async def send_feedback(callback: CallbackQuery, state: FSMContext):
    """Отправка обратной связи"""
    try:
        data = await state.get_data()

        # Сохраняем в БД
        success = db.save_feedback(
            user_id=data['user_id'],
            user_name=data['user_name'],
            feedback_type=data['feedback_type'],
            feedback_text=data['feedback_text'],
            rating=data.get('rating'),
            created_at=datetime.datetime.now()
        )

        if success:
            # Отправляем администраторам
            await send_feedback_to_admins(callback.bot, data)

            await callback.message.edit_text(
                "✅ *Спасибо за вашу обратную связь!*\n\n"
                "Мы ценим ваше мнение и обязательно рассмотрим ваше обращение.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        else:
            await callback.message.edit_text(
                "❌ *Произошла ошибка*\n\nПопробуйте позже.",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )

        await state.clear()
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка отправки feedback: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ Произошла ошибка",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        await callback.answer()


@user_router.callback_query(F.data == "feedback_edit")
async def edit_feedback(callback: CallbackQuery, state: FSMContext):
    """Редактирование обратной связи"""
    await state.set_state(FeedbackStates.waiting_for_feedback_text)

    await callback.message.edit_text(
        "📝 *Исправьте текст:*\n\n"
        "Напишите исправленный вариант:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


async def send_feedback_to_admins(bot, feedback_data):
    """Отправка уведомления о feedback администраторам"""
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

        message_text += (
            f"📄 *Текст:*\n{feedback_data['feedback_text']}\n\n"
            f"🕒 *Время:* {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        for admin_id in config.ADMIN_IDS:
            try:
                await bot.send_message(admin_id, message_text, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Ошибка отправки администратору {admin_id}: {e}")

    except Exception as e:
        logger.error(f"Ошибка send_feedback_to_admins: {e}")


# Функционал кабинета
@user_router.callback_query(F.data == "show_cabinet")
async def show_cabinet(callback: CallbackQuery):
    """Показать личный кабинет пользователя с детальным логированием"""
    try:
        print("\n" + "=" * 70)
        print(f"📱 ОТКРЫТИЕ ЛИЧНОГО КАБИНЕТА")
        print(f"👤 User ID: {callback.from_user.id}")
        print(f"📝 Username: @{callback.from_user.username or 'N/A'}")
        print("=" * 70)

        # ============================================
        # ШАГ 1: Получение user_id из БД
        # ============================================
        print("\n📌 ШАГ 1: Поиск пользователя в БД...")
        query_user = "SELECT id, full_name, phone FROM users WHERE telegram_id = ?"
        user_rows = db.execute_query(query_user, (callback.from_user.id,))

        if not user_rows:
            print("❌ Пользователь не найден в БД")
            await callback.message.edit_text(
                "❌ Вы еще не зарегистрированы.\n\n"
                "Чтобы записаться на курс, нажмите «📝 Новая запись»!",
                reply_markup=get_main_keyboard()
            )
            await callback.answer("Сначала нужно зарегистрироваться")
            return

        user_id = user_rows[0]['id']
        user_name = user_rows[0].get('full_name', 'Не указано')
        user_phone = user_rows[0].get('phone', 'Не указано')

        print(f"✅ Пользователь найден:")
        print(f"  - ID в БД: {user_id}")
        print(f"  - Имя: {user_name}")
        print(f"  - Телефон: {user_phone}")

        # ============================================
        # ШАГ 2: Получение регистраций пользователя
        # ============================================
        print(f"\n📌 ШАГ 2: Поиск регистраций для user_id={user_id}...")

        try:
            # ✅ ИСПРАВЛЕНО: Используем прямой SQL запрос вместо метода репозитория
            query_registrations = """
                                  SELECT r.id, \
                                         r.status_code, \
                                         r.created_at, \
                                         r.updated_at, \
                                         c.name  as course_name, \
                                         tt.name as training_type_name, \
                                         s.name  as schedule_name, \
                                         CASE \
                                             WHEN tt.name LIKE '%Групповые%80%' THEN c.price_group \
                                             WHEN tt.name LIKE '%Индивидуальное%' THEN c.price_individual \
                                             WHEN tt.name LIKE '%Групповые%60%' THEN c.price_group \
                                             ELSE c.price_group \
                                             END as price
                                  FROM registrations r
                                           LEFT JOIN courses c ON r.course_id = c.id
                                           LEFT JOIN training_types tt ON r.training_type_id = tt.id
                                           LEFT JOIN schedules s ON r.schedule_id = s.id
                                  WHERE r.user_id = ?
                                  ORDER BY r.created_at DESC \
                                  """

            registrations = db.execute_query(query_registrations, (user_id,))

            print(f"✅ Найдено регистраций: {len(registrations) if registrations else 0}")

            if registrations:
                print(f"📋 Список регистраций:")
                for reg in registrations:
                    print(f"  - Регистрация #{reg.get('id', 'N/A')}")
                    print(f"    Курс: {reg.get('course_name', 'N/A')}")
                    print(f"    Статус: {reg.get('status_code', 'N/A')}")
                    print(f"    Дата: {reg.get('created_at', 'N/A')}")

        except Exception as e:
            print(f"❌ Ошибка получения регистраций: {e}")
            registrations = []

        # ============================================
        # ШАГ 3: Формирование и отправка ответа
        # ============================================
        print(f"\n📌 ШАГ 3: Формирование ответа пользователю...")

        if not registrations:
            print("ℹ️ У пользователя нет регистраций")
            await callback.message.edit_text(
                f"👤 *Личный кабинет*\n\n"
                f"📝 Имя: {user_name}\n"
                f"📞 Телефон: {user_phone}\n\n"
                f"У вас пока нет активных записей.\n\n"
                f"Хотите записаться на курс? Нажмите «📝 Новая запись»!",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            await callback.answer("У вас пока нет записей")
            print("✅ Сообщение отправлено")
            return

        # Формируем текст с информацией о регистрациях
        cabinet_text = f"👤 *Личный кабинет*\n\n"
        cabinet_text += f"📝 Имя: {user_name}\n"
        cabinet_text += f"📞 Телефон: {user_phone}\n"
        cabinet_text += f"📊 Записей: {len(registrations)}\n\n"
        cabinet_text += f"📋 *Ваши записи:*\n\n"

        for idx, reg in enumerate(registrations, 1):
            status_emoji = {
                'active': '🟢',
                'trial': '🟡',
                'studying': '🔵',
                'frozen': '⚪',
                'waiting_payment': '🟠',
                'completed': '🟣'
            }.get(reg.get('status_code', 'trial'), '⚫')

            status_name = config.STATUSES.get(reg.get('status_code', 'trial'), 'Неизвестно')

            # Форматируем цену
            price = reg.get('price')
            price_text = f"{price:,}".replace(',', ' ') + ' сум' if price else 'Не указана'

            cabinet_text += f"{idx}. {status_emoji} *Запись #{reg.get('id', 'N/A')}*\n"
            cabinet_text += f"   🎓 {reg.get('course_name', 'N/A')}\n"
            cabinet_text += f"   📊 {reg.get('training_type_name', 'N/A')}\n"
            cabinet_text += f"   ⏰ {reg.get('schedule_name', 'N/A')}\n"
            cabinet_text += f"   💰 {price_text}\n"
            cabinet_text += f"   📌 Статус: {status_name}\n"

            # Форматируем дату
            created_at = reg.get('created_at', '')
            if created_at:
                # Обрезаем до даты, если есть время
                date_only = created_at.split()[0] if ' ' in created_at else created_at
                cabinet_text += f"   📅 {date_only}\n\n"
            else:
                cabinet_text += "\n"

        print(f"✅ Текст сформирован ({len(cabinet_text)} символов)")

        await callback.message.edit_text(
            cabinet_text,
            parse_mode="Markdown",
            reply_markup=get_cabinet_keyboard(has_registrations=True)
        )
        await callback.answer("Личный кабинет")

        print("✅ Кабинет успешно отображен")
        print("=" * 70 + "\n")

        logger.info(f"✅ User {callback.from_user.id} opened cabinet with {len(registrations)} registrations")

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ ❌ ❌ ОШИБКА ОТКРЫТИЯ КАБИНЕТА!")
        print(f"Тип ошибки: {type(e).__name__}")
        print(f"Сообщение: {str(e)}")
        print("=" * 70 + "\n")

        logger.error(f"❌ Error in show_cabinet: {e}", exc_info=True)

        try:
            await callback.message.edit_text(
                "❌ Произошла ошибка при открытии кабинета.\n\n"
                "Попробуйте позже или обратитесь в поддержку.",
                reply_markup=get_main_keyboard()
            )
        except:
            # Если не можем отредактировать сообщение, отправим новое
            await callback.message.answer(
                "❌ Произошла ошибка при открытии кабинета.\n\n"
                "Попробуйте позже или обратитесь в поддержку.",
                reply_markup=get_main_keyboard()
            )

        await callback.answer("Ошибка открытия кабинета")


@user_router.callback_query(F.data == "show_materials")
async def show_materials(callback: CallbackQuery):
    """Показать материалы курса"""
    try:
        # Получаем user_id
        query_user = "SELECT id FROM users WHERE telegram_id = ?"
        user_rows = db.execute_query(query_user, (callback.from_user.id,))

        if not user_rows:
            await callback.message.edit_text(
                "❌ Вы еще не зарегистрированы.",
                reply_markup=get_main_keyboard()
            )
            await callback.answer()
            return

        user_id = user_rows[0]['id']

        # ✅ ИСПРАВЛЕНО: Прямой SQL запрос
        query = """
                SELECT r.*, c.name as course_name
                FROM registrations r
                         LEFT JOIN courses c ON r.course_id = c.id
                WHERE r.user_id = ?
                ORDER BY r.created_at DESC \
                """
        registrations = db.execute_query(query, (user_id,))

        if not registrations:
            await callback.message.edit_text(
                "❌ У вас нет активных курсов.",
                reply_markup=get_main_keyboard()
            )
            await callback.answer()
            return

        # Берем первый курс
        course = registrations[0].get('course_name', 'Неизвестный курс')

        await callback.message.edit_text(
            f"📚 Материалы по курсу {course}:",
            reply_markup=get_materials_keyboard(course)
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в show_materials: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard()
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
    try:
        # Получаем user_id
        query_user = "SELECT id FROM users WHERE telegram_id = ?"
        user_rows = db.execute_query(query_user, (callback.from_user.id,))

        if not user_rows:
            await callback.message.edit_text(
                "❌ Вы еще не зарегистрированы.",
                reply_markup=get_main_keyboard()
            )
            await callback.answer()
            return

        user_id = user_rows[0]['id']

        # ✅ ИСПРАВЛЕНО: Прямой SQL запрос
        query = """
                SELECT r.*, c.name as course_name
                FROM registrations r
                         LEFT JOIN courses c ON r.course_id = c.id
                WHERE r.user_id = ?
                ORDER BY r.created_at DESC \
                """
        registrations = db.execute_query(query, (user_id,))

        if not registrations:
            await callback.message.edit_text(
                "❌ У вас нет активных курсов для отображения прогресса.",
                reply_markup=get_main_keyboard()
            )
            await callback.answer()
            return

        # Формируем текст прогресса
        progress_text = "📊 *Ваш прогресс:*\n\n"

        for reg in registrations:
            course_name = reg.get('course_name', 'Неизвестный курс')
            status = reg.get('status_code', 'trial')

            # Эмодзи для статуса
            status_emoji = {
                'trial': '🟡',
                'studying': '🔵',
                'completed': '🟣',
                'frozen': '⚪'
            }.get(status, '⚫')

            progress_text += f"{status_emoji} *{course_name}*\n"
            progress_text += f"   Статус: {config.STATUSES.get(status, status)}\n\n"

        await callback.message.edit_text(
            progress_text,
            parse_mode="Markdown",
            reply_markup=get_progress_keyboard()
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в show_progress: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        await callback.answer()


@user_router.callback_query(F.data == "start_quiz")
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    """Начать тест/викторину"""
    try:
        # Получаем user_id
        query_user = "SELECT id FROM users WHERE telegram_id = ?"
        user_rows = db.execute_query(query_user, (callback.from_user.id,))

        if not user_rows:
            await callback.message.edit_text(
                "❌ Вы еще не зарегистрированы.",
                reply_markup=get_main_keyboard()
            )
            await callback.answer()
            return

        user_id = user_rows[0]['id']

        # ✅ ИСПРАВЛЕНО: Прямой SQL запрос
        query = """
                SELECT r.*, c.name as course_name
                FROM registrations r
                         LEFT JOIN courses c ON r.course_id = c.id
                WHERE r.user_id = ?
                ORDER BY r.created_at DESC \
                """
        registrations = db.execute_query(query, (user_id,))

        if not registrations:
            await callback.message.edit_text(
                "❌ У вас нет активных курсов для прохождения тестов.",
                reply_markup=get_main_keyboard()
            )
            await callback.answer()
            return

        # Берем первый курс
        course_name = registrations[0].get('course_name', '')

        # Проверяем, есть ли тесты для этого курса
        if course_name not in config.QUIZZES:
            await callback.message.edit_text(
                f"❌ Для курса {course_name} пока нет доступных тестов.",
                reply_markup=get_cabinet_keyboard()
            )
            await callback.answer()
            return

        # Начинаем тест
        questions = config.QUIZZES[course_name]
        await state.update_data(
            course=course_name,
            questions=questions,
            current_question=0,
            correct_answers=0
        )

        # Показываем первый вопрос
        question = questions[0]
        await callback.message.edit_text(
            f"🎯 *Тест: {course_name}*\n\n"
            f"Вопрос 1 из {len(questions)}:\n\n"
            f"{question['question']}",
            parse_mode="Markdown",
            reply_markup=get_quiz_question_keyboard(0, question['options'])
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в start_quiz: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
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
        reply_markup=get_quiz_question_keyboard(question_index, question['options'])
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
    # Получаем user_id по telegram_id
    query_user = "SELECT id FROM users WHERE telegram_id = ?"
    user_rows = db.execute_query(query_user, (callback.from_user.id,))
    if not user_rows:
        await callback.message.edit_text("Вы еще не зарегистрированы.", reply_markup=get_main_keyboard())
        return

    user_id = user_rows[0]['id']

    # Получаем регистрации пользователя
    db.execute_query("""
                     SELECT r.*, c.name as course_name
                     FROM registrations r
                              LEFT JOIN courses c ON r.course_id = c.id
                     WHERE r.user_id = ?
                     ORDER BY r.created_at DESC
                     """, (user_id,))

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
    """Отмена действия"""
    await state.clear()

    await callback.message.edit_text(
        "❌ Отменено",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@user_router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()

    try:
        await callback.message.edit_text(
            "🏠 *Главное меню*\n\nВыберите действие:",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    except aiogram.exceptions.TelegramBadRequest:
        await callback.message.answer(
            "🏠 *Главное меню*\n\nВыберите действие:",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

    await callback.answer()


@user_router.callback_query(F.data == "about_center")
async def about_center(callback: CallbackQuery):
    """Информация о центре"""
    about_text = (
        "🏫 *О нашем образовательном центре*\n\n"
        "Мы предоставляем качественное образование по различным направлениям.\n\n"
        "📞 *Контакты:*\n"
        "Телефон: +998 XX XXX-XX-XX\n"
        "Email: info@example.com\n"
        "Адрес: г. Ташкент, ул. ...\n\n"
        "🕒 *Часы работы:*\n"
        "Пн-Пт: 9:00-18:00\n"
        "Сб: 10:00-15:00\n"
        "Вс: выходной"
    )

    await callback.message.edit_text(
        about_text,
        parse_mode="Markdown",
        reply_markup=get_back_keyboard("back_to_main")
    )
    await callback.answer()


@user_router.callback_query(F.data == "show_courses")
async def show_courses(callback: CallbackQuery):
    """Показать список курсов"""
    courses_text = "🎓 *Доступные курсы:*\n\n"

    for course, types_dict in config.COURSES.items():
        courses_text += f"*{course}:*\n"
        for training_type, price in types_dict.items():
            courses_text += f"  • {training_type}: {price}\n"
        courses_text += "\n"

    await callback.message.edit_text(
        courses_text,
        parse_mode="Markdown",
        reply_markup=get_back_keyboard("back_to_main")
    )
    await callback.answer()

    @user_router.callback_query(F.data == "my_registrations")
    async def show_my_registrations(callback: CallbackQuery):
        """Показать список записей пользователя"""
        try:
            # Получаем user_id по telegram_id
            query_user = "SELECT id FROM users WHERE telegram_id = ?"
            user_rows = db.execute_query(query_user, (callback.from_user.id,))

            if not user_rows:
                await callback.message.edit_text(
                    "Вы еще не зарегистрированы.",
                    reply_markup=get_main_keyboard()
                )
                await callback.answer()
                return

            user_id = user_rows[0]['id']

            # Получаем регистрации пользователя
            registrations = db.registrations.get_by_user_id(user_id)

            if not registrations:
                await callback.message.edit_text(
                    "📝 *У вас пока нет записей на курсы*\n\n"
                    "Хотите записаться на курс?",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📝 Записаться на курс", callback_data="new_registration")],
                        [InlineKeyboardButton(text="◀️ Назад", callback_data="show_cabinet")]
                    ])
                )
            else:
                text = "📋 *Ваши записи на курсы:*\n\n"

                for idx, reg in enumerate(registrations, 1):
                    status_emoji = {
                        'active': '🟢',
                        'trial': '🟡',
                        'studying': '🔵',
                        'frozen': '⚪',
                        'waiting_payment': '🟠',
                        'completed': '🟣'
                    }.get(reg['status_code'], '⚫')

                    status_text = config.STATUSES.get(reg['status_code'], reg['status_code'])

                    text += (
                        f"*{idx}. {reg['course_name']}* {status_emoji}\n"
                        f"   📊 Статус: {status_text}\n"
                        f"   📅 Дата: {reg['created_at'][:10]}\n\n"
                    )

                await callback.message.edit_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=get_registrations_keyboard(registrations)
                )

            await callback.answer()

        except Exception as e:
            logger.error(f"Ошибка в show_my_registrations: {str(e)}", exc_info=True)
            try:
                await callback.message.edit_text(
                    text="❌ *Произошла ошибка*\n\n"
                         "Не удалось загрузить список записей. Пожалуйста, попробуйте позже.",
                    parse_mode="Markdown",
                    reply_markup=get_cabinet_keyboard()
                )
            except Exception as edit_error:
                logger.error(f"Не удалось отредактировать сообщение: {edit_error}")

            await callback.answer()


@user_router.callback_query(F.data.startswith("registration_detail_"))
async def show_registration_detail(callback: CallbackQuery):
    """✅ ИСПРАВЛЕНО: Показать детальную информацию о регистрации"""
    try:
        # Извлекаем ID регистрации
        reg_id = int(callback.data.replace("registration_detail_", ""))

        # Получаем регистрацию (✅ ИСПРАВЛЕНА ЗАКРЫВАЮЩАЯ СКОБКА)
        registration = db.get_registration_by_id(reg_id)

        if not registration:
            await callback.message.edit_text(
                "❌ Регистрация не найдена",
                reply_markup=get_back_keyboard("my_registrations", "◀️ К списку записей")
            )
            await callback.answer()
            return

        # Формируем детальную информацию
        status_emoji = {
            'active': '🟢',
            'trial': '🟡',
            'studying': '🔵',
            'frozen': '⚪',
            'waiting_payment': '🟠',
            'completed': '🟣'
        }.get(registration.status, '⚫')

        status_text = config.STATUSES.get(registration.status, registration.status)

        detail_text = (
            f"📋 *Детали записи* {status_emoji}\n\n"
            f"🎓 *Курс:* {registration.course}\n"
            f"📊 *Тип обучения:* {registration.training_type}\n"
            f"⏰ *Расписание:* {registration.schedule}\n"
            f"💰 *Стоимость:* {registration.price}\n"
            f"📌 *Статус:* {status_text}\n"
        )

        if registration.created_at:
            detail_text += f"📅 *Дата записи:* {registration.created_at.strftime('%d.%m.%Y %H:%M')}\n"

        await callback.message.edit_text(
            detail_text,
            parse_mode="Markdown",
            reply_markup=get_registration_detail_keyboard(registration.id)
        )
        await callback.answer()

    except ValueError:
        logger.error(f"Неверный формат ID в registration_detail: {callback.data}")
        await callback.answer("❌ Ошибка: неверный формат данных", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в show_registration_detail: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке информации",
            reply_markup=get_back_keyboard("my_registrations", "◀️ К списку записей")
        )
        await callback.answer()


@user_router.callback_query(F.data == "show_materials")
async def show_my_materials(callback: CallbackQuery):
    """✅ ИСПРАВЛЕНО: Показать материалы курсов"""
    try:
        # Получаем пользователя (✅ ИСПРАВЛЕНА ЗАКРЫВАЮЩАЯ СКОБКА)
        user = db.get_user_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.message.edit_text(
                "❌ Пользователь не найден",
                reply_markup=get_cabinet_keyboard()
            )
            await callback.answer()
            return

        # Получаем активные регистрации пользователя
        registrations = db.get_registrations_by_user_id(user.id)
        active_registrations = [r for r in registrations if r.status in ['active', 'studying']]

        if not active_registrations:
            await callback.message.edit_text(
                "📚 *Материалы курсов*\n\n"
                "У вас пока нет активных курсов.\n"
                "Запишитесь на курс, чтобы получить доступ к материалам!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📝 Записаться на курс", callback_data="new_registration")],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="show_cabinet")]
                ])
            )
            await callback.answer()
            return

        # Собираем уникальные курсы
        courses = list(set([r.course for r in active_registrations]))

        # Формируем клавиатуру с материалами
        buttons = []

        for course in courses:
            if course in config.MATERIALS:
                materials = config.MATERIALS[course]

                # Добавляем заголовок курса
                buttons.append([InlineKeyboardButton(
                    text=f"📚 {course}",
                    callback_data=f"materials_course_{course}"
                )])

                # Добавляем ссылки на материалы
                for title, url in materials.items():
                    buttons.append([InlineKeyboardButton(text=f"  📄 {title}", url=url)])

        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="show_cabinet")])

        await callback.message.edit_text(
            "📚 *Материалы ваших курсов:*\n\n"
            "Выберите материал для просмотра:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в show_my_materials: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке материалов",
            reply_markup=get_cabinet_keyboard()
        )
        await callback.answer()


@user_router.callback_query(F.data == "show_progress")
async def show_my_progress(callback: CallbackQuery):
    """✅ ИСПРАВЛЕНО: Показать прогресс обучения"""
    try:
        # Получаем пользователя (✅ ИСПРАВЛЕНА ЗАКРЫВАЮЩАЯ СКОБКА)
        user = db.get_user_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.message.edit_text(
                "❌ Пользователь не найден",
                reply_markup=get_cabinet_keyboard()
            )
            await callback.answer()
            return

        # Получаем регистрации
        registrations = db.get_registrations_by_user_id(user.id)

        if not registrations:
            await callback.message.edit_text(
                "📊 *Ваш прогресс*\n\n"
                "У вас пока нет записей на курсы.\n"
                "Запишитесь на курс, чтобы отслеживать свой прогресс!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📝 Записаться на курс", callback_data="new_registration")],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="show_cabinet")]
                ])
            )
            await callback.answer()
            return

        # Собираем статистику
        total_courses = len(registrations)
        active_courses = len([r for r in registrations if r.status in ['active', 'studying']])
        completed_courses = len([r for r in registrations if r.status == 'completed'])

        progress_text = (
            "📊 *Ваш прогресс обучения*\n\n"
            f"📚 Всего курсов: {total_courses}\n"
            f"🔵 Активных: {active_courses}\n"
            f"🟣 Завершено: {completed_courses}\n\n"
        )

        # Добавляем информацию по каждому курсу
        if active_courses > 0:
            progress_text += "*Активные курсы:*\n"
            for reg in registrations:
                if reg['status_code'] in ['active', 'studying']:
                    progress_text += f"• {reg['course_name']} - {config.STATUSES.get(reg['status_code'], reg['status_code'])}\n"

        await callback.message.edit_text(
            progress_text,
            parse_mode="Markdown",
            reply_markup=get_progress_keyboard()
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в show_my_progress: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке прогресса",
            reply_markup=get_cabinet_keyboard()
        )
        await callback.answer()


@user_router.callback_query(F.data == "my_schedule")
async def show_my_schedule(callback: CallbackQuery):
    """Показать расписание пользователя"""
    try:
        # ✅ ИСПРАВЛЕНО: Прямой SQL запрос
        query = "SELECT * FROM users WHERE telegram_id = ?"
        users = db.execute_query(query, (callback.from_user.id,))
        user = users[0] if users else None

        if not user:
            await callback.message.edit_text(
                "❌ Пользователь не найден. Пожалуйста, сначала зарегистрируйтесь.",
                reply_markup=get_main_keyboard()
            )
            await callback.answer()
            return

        user_id = user['id']

        # Получаем регистрации пользователя
        query_reg = """
                    SELECT r.*, \
                           c.name as course_name, \
                           s.name as schedule_name, \
                           s.time_start, \
                           s.time_end
                    FROM registrations r
                             LEFT JOIN courses c ON r.course_id = c.id
                             LEFT JOIN schedules s ON r.schedule_id = s.id
                    WHERE r.user_id = ?
                    ORDER BY r.created_at DESC \
                    """
        registrations = db.execute_query(query_reg, (user_id,))

        if not registrations:
            await callback.message.edit_text(
                "❌ У вас нет активных записей с расписанием.",
                reply_markup=get_cabinet_keyboard()
            )
            await callback.answer()
            return

        # Формируем текст расписания
        schedule_text = "📅 *Ваше расписание:*\n\n"

        for reg in registrations:
            course_name = reg.get('course_name', 'Неизвестный курс')
            schedule_name = reg.get('schedule_name', 'Не указано')
            time_start = reg.get('time_start', '')
            time_end = reg.get('time_end', '')

            schedule_text += f"📚 *{course_name}*\n"
            schedule_text += f"   ⏰ {schedule_name}\n"

            if time_start and time_end:
                schedule_text += f"   🕐 {time_start} - {time_end}\n"

            schedule_text += "\n"

        await callback.message.edit_text(
            schedule_text,
            parse_mode="Markdown",
            reply_markup=get_back_keyboard("show_cabinet")
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в show_my_schedule: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_keyboard()
        )
        await callback.answer()


@user_router.callback_query(F.data == "start_quiz")
async def show_quiz_menu(callback: CallbackQuery):
    """✅ ИСПРАВЛЕНО: Показать меню тестов"""
    try:
        # Получаем пользователя (✅ ИСПРАВЛЕНА ЗАКРЫВАЮЩАЯ СКОБКА)
        user = db.get_user_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.message.edit_text(
                "❌ Пользователь не найден",
                reply_markup=get_cabinet_keyboard()
            )
            await callback.answer()
            return

        # Получаем активные курсы
        registrations = db.get_registrations_by_user_id(user.id)
        active_registrations = [r for r in registrations if r.status in ['active', 'studying']]

        if not active_registrations:
            await callback.message.edit_text(
                "🎯 *Тесты и викторины*\n\n"
                "У вас пока нет активных курсов.\n"
                "Запишитесь на курс, чтобы проходить тесты!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📝 Записаться на курс", callback_data="new_registration")],
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="show_cabinet")]
                ])
            )
            await callback.answer()
            return

        # Формируем список курсов с тестами
        buttons = []
        has_quizzes = False

        for reg in active_registrations:
            if reg['course_name'] in config.QUIZZES:
                has_quizzes = True
                buttons.append([InlineKeyboardButton(
                    text=f"🎯 {reg['course_name']}",
                    callback_data=f"quiz_course_{reg['course_name']}"
                )])

        if not has_quizzes:
            await callback.message.edit_text(
                "🎯 *Тесты и викторины*\n\n"
                "Для ваших курсов пока нет доступных тестов.",
                parse_mode="Markdown",
                reply_markup=get_back_keyboard("show_cabinet")
            )
        else:
            buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="show_cabinet")])

            await callback.message.edit_text(
                "🎯 *Выберите курс для прохождения теста:*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
            )

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в show_quiz_menu: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке тестов",
            reply_markup=get_cabinet_keyboard()
        )
        await callback.answer()


def register_user_handlers(dp):
    """Регистрация пользовательских обработчиков"""
    dp.include_router(user_router)
