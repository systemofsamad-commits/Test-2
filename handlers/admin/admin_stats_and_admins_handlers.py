import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.admin_states import AdminStates
from database import Database
from helpers import is_admin
from config import Config

logger = logging.getLogger(__name__)
router = Router(name="admin_stats_and_admins_handlers")
config = Config()
db = Database(config.DB_NAME)


# ============ СТАТИСТИКА ============

@router.callback_query(F.data == "show_general_stats")
async def show_general_stats(callback: CallbackQuery):
    """Показать общую статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    try:
        # Получаем все регистрации
        all_students = db.get_all_registrations()

        # Считаем по статусам
        stats_by_status = {}
        for status_key, status_name in config.STATUSES.items():
            students = db.get_students_by_status(status_key)
            stats_by_status[status_name] = len(students)

        # Общая статистика
        total_students = len(all_students)

        # Формируем текст
        text = "📊 *Общая статистика*\n\n"
        text += f"👥 *Всего студентов:* {total_students}\n\n"

        text += "📈 *По статусам:*\n"
        for status_name, count in stats_by_status.items():
            percentage = (count / total_students * 100) if total_students > 0 else 0
            text += f"  • {status_name}: {count} ({percentage:.1f}%)\n"

        # Статистика по курсам
        text += "\n📚 *По курсам:*\n"
        courses_stats = {}
        for student in all_students:
            course = student.course
            courses_stats[course] = courses_stats.get(course, 0) + 1

        for course, count in sorted(courses_stats.items(), key=lambda x: x[1], reverse=True):
            text += f"  • {course}: {count} чел.\n"

        from keyboards.admin_kb import get_admin_stats_menu
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_admin_stats_menu()
        )

    except Exception as e:
        logger.error(f"Error in show_general_stats: {e}")
        await callback.answer("❌ Ошибка получения статистики")

    await callback.answer()


@router.callback_query(F.data == "show_weekly_stats")
async def show_weekly_stats(callback: CallbackQuery):
    """Показать недельную статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    try:
        stats = db.get_weekly_stats()

        text = "📅 *Статистика за неделю*\n\n"

        text += f"📝 *Новых регистраций:* {stats.get('new_registrations', 0)}\n"
        text += f"✅ *Завершили обучение:* {stats.get('completed', 0)}\n"
        text += f"❄️ *Заморожено:* {stats.get('frozen', 0)}\n"
        text += f"🎓 *Начали обучение:* {stats.get('started_studying', 0)}\n\n"

        # Активность по дням
        if 'daily' in stats:
            text += "📊 *По дням недели:*\n"
            days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
            for i, count in enumerate(stats['daily']):
                text += f"  {days[i]}: {count} рег.\n"

        from keyboards.admin_kb import get_admin_stats_menu
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_admin_stats_menu()
        )

    except Exception as e:
        logger.error(f"Error in show_weekly_stats: {e}")
        await callback.answer("❌ Ошибка получения статистики")

    await callback.answer()


@router.callback_query(F.data == "show_feedback_stats")
async def show_feedback_stats(callback: CallbackQuery):
    """Показать статистику обратной связи"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    try:
        stats = db.get_feedback_stats()

        text = "💬 *Статистика обратной связи*\n\n"

        text += f"📝 *Всего отзывов:* {stats.get('total', 0)}\n\n"

        # По типам
        text += "📋 *По типам:*\n"
        text += f"  ⭐ Отзывы: {stats.get('reviews', 0)}\n"
        text += f"  💡 Предложения: {stats.get('suggestions', 0)}\n"
        text += f"  🐞 Проблемы: {stats.get('issues', 0)}\n\n"

        # Средняя оценка
        if stats.get('avg_rating'):
            text += f"⭐ *Средняя оценка:* {stats['avg_rating']:.1f}/5\n\n"

        # Распределение оценок
        if 'rating_distribution' in stats:
            text += "📊 *Распределение оценок:*\n"
            for rating in range(5, 0, -1):
                count = stats['rating_distribution'].get(rating, 0)
                stars = "⭐" * rating
                text += f"  {stars}: {count}\n"

        from keyboards.admin_kb import get_admin_stats_menu
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_admin_stats_menu()
        )

    except Exception as e:
        logger.error(f"Error in show_feedback_stats: {e}")
        await callback.answer("❌ Ошибка получения статистики")

    await callback.answer()


@router.callback_query(F.data == "show_payment_stats")
async def show_payment_stats(callback: CallbackQuery):
    """Показать статистику по оплатам"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    try:
        # Получаем студентов по статусам
        waiting_payment = db.get_students_by_status('waiting_payment')
        studying = db.get_students_by_status('studying')
        completed = db.get_students_by_status('completed')

        text = "💰 *Статистика по оплатам*\n\n"

        text += f"🟠 *Ожидают оплаты:* {len(waiting_payment)} чел.\n"
        text += f"🔵 *Оплатили и обучаются:* {len(studying)} чел.\n"
        text += f"🟣 *Завершили курс:* {len(completed)} чел.\n\n"

        # Потенциальный доход от ожидающих
        if waiting_payment:
            text += "💵 *От ожидающих оплату:*\n"
            total_potential = 0
            for student in waiting_payment:
                try:
                    # Извлекаем число из строки цены
                    price_str = student.price.replace(',', '').replace(' ', '')
                    import re
                    price_match = re.search(r'\d+', price_str)
                    if price_match:
                        total_potential += int(price_match.group())
                except:
                    pass

            if total_potential > 0:
                text += f"  Потенциальный доход: ~{total_potential:,} сум\n\n"

        # Список ожидающих оплату
        if waiting_payment and len(waiting_payment) <= 10:
            text += "👥 *Список ожидающих:*\n"
            for student in waiting_payment[:10]:
                text += f"  • {student.name} - {student.course}\n"

        from keyboards.admin_kb import get_admin_stats_menu
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_admin_stats_menu()
        )

    except Exception as e:
        logger.error(f"Error in show_payment_stats: {e}")
        await callback.answer("❌ Ошибка получения статистики")

    await callback.answer()


# ============ УПРАВЛЕНИЕ АДМИНИСТРАТОРАМИ ============

@router.callback_query(F.data == "add_admin")
async def add_admin_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления администратора"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await state.set_state(AdminStates.waiting_for_admin_id)

    from keyboards.admin_kb import get_cancel_keyboard
    await callback.message.edit_text(
        "👤 *Добавление администратора*\n\n"
        "Введите Telegram ID пользователя:\n\n"
        "💡 *Как узнать ID:*\n"
        "1. Попросите пользователя написать боту @userinfobot\n"
        "2. Бот покажет его ID\n"
        "3. Введите полученный ID",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_admin_id)
async def process_admin_id(message: Message, state: FSMContext):
    """Обработка ID нового администратора"""
    if not is_admin(message.from_user.id):
        return

    if message.text in ["❌ Отмена", "◀️ Назад"]:
        await state.clear()
        from keyboards.admin_kb import get_admin_admins_menu
        await message.answer("❌ Добавление администратора отменено.",
                             reply_markup=get_admin_admins_menu())
        return

    try:
        admin_id = int(message.text.strip())

        # Проверка что это не сам пользователь
        if admin_id == message.from_user.id:
            await message.answer("❌ Вы уже являетесь администратором!")
            return

        # Проверка что администратор ещё не добавлен
        if db.is_admin(admin_id):
            await message.answer(f"⚠️ Пользователь {admin_id} уже является администратором!")
            return

        # Добавляем администратора
        success = db.add_admin(admin_id)

        if success:
            from keyboards.admin_kb import get_admin_admins_menu
            await message.answer(
                f"✅ *Администратор добавлен!*\n\n"
                f"👤 ID: `{admin_id}`\n\n"
                f"Теперь этот пользователь имеет доступ к админ-панели.",
                parse_mode="Markdown",
                reply_markup=get_admin_admins_menu()
            )

            # Попытка отправить уведомление новому админу
            try:
                await message.bot.send_message(
                    admin_id,
                    "🎉 *Вы получили права администратора!*\n\n"
                    "Теперь вы можете использовать команду /admin для доступа к панели управления.",
                    parse_mode="Markdown"
                )
            except:
                logger.warning(f"Не удалось отправить уведомление новому админу {admin_id}")
        else:
            from keyboards.admin_kb import get_admin_admins_menu
            await message.answer(
                "❌ Ошибка при добавлении администратора.",
                reply_markup=get_admin_admins_menu()
            )

        await state.clear()

    except ValueError:
        from keyboards.admin_kb import get_cancel_keyboard
        await message.answer(
            "❌ Неверный формат ID. Введите число:",
            reply_markup=get_cancel_keyboard()
        )


@router.callback_query(F.data == "remove_admin")
async def remove_admin_start(callback: CallbackQuery, state: FSMContext):
    """Начало удаления администратора"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    # Получаем список администраторов
    admins = db.get_all_admins()

    if len(admins) <= 1:
        await callback.answer(
            "⚠️ Нельзя удалить последнего администратора!",
            show_alert=True
        )
        return

    await state.set_state(AdminStates.waiting_for_remove_admin_id)

    # Формируем список администраторов
    text = "👤 *Удаление администратора*\n\n"
    text += "📋 *Список администраторов:*\n\n"

    for admin in admins:
        text += f"• ID: `{admin['user_id']}`"
        if admin.get('username'):
            text += f" (@{admin['username']})"
        if admin.get('full_name'):
            text += f"\n  Имя: {admin['full_name']}"
        text += "\n\n"

    text += "Введите ID администратора для удаления:"

    from keyboards.admin_kb import get_cancel_keyboard
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_remove_admin_id)
async def process_remove_admin_id(message: Message, state: FSMContext):
    """Обработка удаления администратора"""
    if not is_admin(message.from_user.id):
        return

    if message.text in ["❌ Отмена", "◀️ Назад"]:
        await state.clear()
        from keyboards.admin_kb import get_admin_admins_menu
        await message.answer("❌ Удаление администратора отменено.",
                             reply_markup=get_admin_admins_menu())
        return

    try:
        admin_id = int(message.text.strip())

        # Проверка что не удаляет сам себя
        if admin_id == message.from_user.id:
            await message.answer("❌ Вы не можете удалить себя из администраторов!")
            return

        # Проверка что это администратор
        if not db.is_admin(admin_id):
            await message.answer(f"⚠️ Пользователь {admin_id} не является администратором!")
            return

        # Удаляем администратора
        success = db.remove_admin(admin_id)

        if success:
            from keyboards.admin_kb import get_admin_admins_menu
            await message.answer(
                f"✅ *Администратор удалён!*\n\n"
                f"👤 ID: `{admin_id}`\n\n"
                f"Этот пользователь больше не имеет доступа к админ-панели.",
                parse_mode="Markdown",
                reply_markup=get_admin_admins_menu()
            )

            # Попытка отправить уведомление удалённому админу
            try:
                await message.bot.send_message(
                    admin_id,
                    "⚠️ *Ваши права администратора были отозваны.*\n\n"
                    "У вас больше нет доступа к панели управления.",
                    parse_mode="Markdown"
                )
            except:
                logger.warning(f"Не удалось отправить уведомление удалённому админу {admin_id}")
        else:
            from keyboards.admin_kb import get_admin_admins_menu
            await message.answer(
                "❌ Ошибка при удалении администратора.",
                reply_markup=get_admin_admins_menu()
            )

        await state.clear()

    except ValueError:
        from keyboards.admin_kb import get_cancel_keyboard
        await message.answer(
            "❌ Неверный формат ID. Введите число:",
            reply_markup=get_cancel_keyboard()
        )


@router.callback_query(F.data == "list_admins")
async def list_admins(callback: CallbackQuery):
    """Показать список администраторов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    admins = db.get_all_admins()

    if not admins:
        text = "📋 Список администраторов пуст"
    else:
        text = "📋 *Список администраторов:*\n\n"
        for i, admin in enumerate(admins, 1):
            text += f"{i}. 👤 ID: `{admin['user_id']}`\n"
            if admin.get('username'):
                text += f"   📱 @{admin['username']}\n"
            if admin.get('full_name'):
                text += f"   📛 {admin['full_name']}\n"
            text += f"   📅 Добавлен: {admin['created_at'][:10]}\n"
            text += f"   🔹 Статус: {'✅ Активен' if admin['is_active'] else '❌ Неактивен'}\n\n"

    from keyboards.admin_kb import get_admin_admins_menu
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_admin_admins_menu()
    )
    await callback.answer()