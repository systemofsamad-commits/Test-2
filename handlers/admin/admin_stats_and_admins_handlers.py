import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.admin_states import AdminStates
from helpers import get_db, is_admin
from config import Config

logger = logging.getLogger(__name__)
router = Router(name="admin_stats_and_admins_handlers")
config = Config()


# ============ СТАТИСТИКА ============

@router.callback_query(F.data == "show_general_stats")
async def show_general_stats(callback: CallbackQuery):
    """Показать общую статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    try:
        db = get_db()

        # ✅ ИСПРАВЛЕНО: Прямой SQL запрос для получения всех регистраций
        query_all = """
                    SELECT r.id, \
                           r.status_code, \
                           r.full_name, \
                           r.phone,
                           c.name as course_name
                    FROM registrations r
                             LEFT JOIN courses c ON r.course_id = c.id \
                    """
        all_students = db.execute_query(query_all)

        # ✅ ИСПРАВЛЕНО: Считаем по статусам через SQL
        stats_by_status = {}
        for status_key, status_name in config.STATUSES.items():
            query = """
                    SELECT COUNT(*) as count
                    FROM registrations
                    WHERE status_code = ? \
                    """
            result = db.execute_query(query, (status_key,))
            count = result[0]['count'] if result else 0
            stats_by_status[status_name] = count

        # Общая статистика
        total_students = len(all_students)

        # Формируем текст
        text = "📊 *Общая статистика*\n\n"
        text += f"👥 *Всего студентов:* {total_students}\n\n"

        text += "📈 *По статусам:*\n"
        for status_name, count in stats_by_status.items():
            percentage = (count / total_students * 100) if total_students > 0 else 0
            text += f"  • {status_name}: {count} ({percentage:.1f}%)\n"

        # ✅ ИСПРАВЛЕНО: Статистика по курсам через SQL
        text += "\n📚 *По курсам:*\n"
        query_courses = """
                        SELECT c.name as course_name, COUNT(r.id) as count
                        FROM registrations r
                                 LEFT JOIN courses c ON r.course_id = c.id
                        GROUP BY c.name
                        ORDER BY count DESC \
                        """
        courses_stats = db.execute_query(query_courses)

        for course in courses_stats:
            if course.get('course_name'):
                text += f"  • {course['course_name']}: {course['count']} чел.\n"

        from keyboards.admin_kb import get_admin_stats_menu
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_admin_stats_menu()
        )

    except Exception as e:
        logger.error(f"Error in show_general_stats: {e}", exc_info=True)
        await callback.answer("❌ Ошибка получения статистики")

    await callback.answer()


@router.callback_query(F.data == "show_weekly_stats")
async def show_weekly_stats(callback: CallbackQuery):
    """Показать недельную статистику"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    try:
        db = get_db()

        # ✅ ИСПРАВЛЕНО: Прямые SQL запросы для недельной статистики
        # Новые регистрации за неделю
        query_new = """
                    SELECT COUNT(*) as count
                    FROM registrations
                    WHERE created_at >= datetime('now', '-7 days') \
                    """
        new_reg_result = db.execute_query(query_new)
        new_registrations = new_reg_result[0]['count'] if new_reg_result else 0

        # Завершили обучение за неделю
        query_completed = """
                          SELECT COUNT(*) as count
                          FROM registrations
                          WHERE status_code = 'completed'
                            AND updated_at >= datetime('now', '-7 days') \
                          """
        completed_result = db.execute_query(query_completed)
        completed = completed_result[0]['count'] if completed_result else 0

        # Заморожено за неделю
        query_frozen = """
                       SELECT COUNT(*) as count
                       FROM registrations
                       WHERE status_code = 'frozen'
                         AND updated_at >= datetime('now', '-7 days') \
                       """
        frozen_result = db.execute_query(query_frozen)
        frozen = frozen_result[0]['count'] if frozen_result else 0

        # Начали обучение за неделю
        query_started = """
                        SELECT COUNT(*) as count
                        FROM registrations
                        WHERE status_code = 'studying'
                          AND updated_at >= datetime('now', '-7 days') \
                        """
        started_result = db.execute_query(query_started)
        started_studying = started_result[0]['count'] if started_result else 0

        text = "📅 *Статистика за неделю*\n\n"
        text += f"📝 *Новых регистраций:* {new_registrations}\n"
        text += f"✅ *Завершили обучение:* {completed}\n"
        text += f"❄️ *Заморожено:* {frozen}\n"
        text += f"🎓 *Начали обучение:* {started_studying}\n\n"

        from keyboards.admin_kb import get_admin_stats_menu
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_admin_stats_menu()
        )

    except Exception as e:
        logger.error(f"Error in show_weekly_stats: {e}", exc_info=True)
        await callback.answer("❌ Ошибка получения статистики")

    await callback.answer()


@router.callback_query(F.data == "show_feedback_stats")
async def show_feedback_stats(callback: CallbackQuery):
    """Показать статистику обратной связи"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    try:
        db = get_db()

        # ✅ ИСПРАВЛЕНО: Прямые SQL запросы для статистики отзывов
        # Проверяем наличие таблицы feedback
        check_table = """
                      SELECT name \
                      FROM sqlite_master
                      WHERE type = 'table' \
                        AND name = 'feedback' \
                      """
        table_exists = db.execute_query(check_table)

        if not table_exists:
            text = "💬 *Статистика обратной связи*\n\n"
            text += "📝 Таблица отзывов не найдена.\n"
            text += "Функция находится в разработке."
        else:
            # Общее количество
            query_total = "SELECT COUNT(*) as count FROM feedback"
            total_result = db.execute_query(query_total)
            total = total_result[0]['count'] if total_result else 0

            # По типам
            query_reviews = "SELECT COUNT(*) as count FROM feedback WHERE type = 'review'"
            reviews_result = db.execute_query(query_reviews)
            reviews = reviews_result[0]['count'] if reviews_result else 0

            query_suggestions = "SELECT COUNT(*) as count FROM feedback WHERE type = 'suggestion'"
            suggestions_result = db.execute_query(query_suggestions)
            suggestions = suggestions_result[0]['count'] if suggestions_result else 0

            query_issues = "SELECT COUNT(*) as count FROM feedback WHERE type = 'issue'"
            issues_result = db.execute_query(query_issues)
            issues = issues_result[0]['count'] if issues_result else 0

            # Средняя оценка
            query_avg = "SELECT AVG(rating) as avg_rating FROM feedback WHERE rating IS NOT NULL"
            avg_result = db.execute_query(query_avg)
            avg_rating = avg_result[0]['avg_rating'] if avg_result and avg_result[0]['avg_rating'] else 0

            text = "💬 *Статистика обратной связи*\n\n"
            text += f"📝 *Всего отзывов:* {total}\n\n"
            text += "📋 *По типам:*\n"
            text += f"  ⭐ Отзывы: {reviews}\n"
            text += f"  💡 Предложения: {suggestions}\n"
            text += f"  🐞 Проблемы: {issues}\n\n"

            if avg_rating > 0:
                text += f"⭐ *Средняя оценка:* {avg_rating:.1f}/5\n"

        from keyboards.admin_kb import get_admin_stats_menu
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_admin_stats_menu()
        )

    except Exception as e:
        logger.error(f"Error in show_feedback_stats: {e}", exc_info=True)
        await callback.answer("❌ Ошибка получения статистики")

    await callback.answer()


@router.callback_query(F.data == "show_payment_stats")
async def show_payment_stats(callback: CallbackQuery):
    """Показать статистику по оплатам"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    try:
        db = get_db()

        # ✅ ИСПРАВЛЕНО: Прямые SQL запросы для получения студентов по статусам
        query_waiting = """
                        SELECT r.id, \
                               r.full_name as name, \
                               r.phone,
                               c.name      as course_name
                        FROM registrations r
                                 LEFT JOIN courses c ON r.course_id = c.id
                        WHERE r.status_code = 'waiting_payment' \
                        """
        waiting_payment = db.execute_query(query_waiting)

        query_studying = """
                         SELECT COUNT(*) as count
                         FROM registrations
                         WHERE status_code = 'studying' \
                         """
        studying_result = db.execute_query(query_studying)
        studying_count = studying_result[0]['count'] if studying_result else 0

        query_completed = """
                          SELECT COUNT(*) as count
                          FROM registrations
                          WHERE status_code = 'completed' \
                          """
        completed_result = db.execute_query(query_completed)
        completed_count = completed_result[0]['count'] if completed_result else 0

        text = "💰 *Статистика по оплатам*\n\n"
        text += f"🟠 *Ожидают оплаты:* {len(waiting_payment)} чел.\n"
        text += f"🔵 *Оплатили и обучаются:* {studying_count} чел.\n"
        text += f"🟣 *Завершили курс:* {completed_count} чел.\n\n"

        # Список ожидающих оплату
        if waiting_payment and len(waiting_payment) <= 10:
            text += "👥 *Список ожидающих:*\n"
            for student in waiting_payment[:10]:
                course = student.get('course_name', 'Не указан')
                name = student.get('name', 'Не указано')
                text += f"  • {name} - {course}\n"

        from keyboards.admin_kb import get_admin_stats_menu
        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_admin_stats_menu()
        )

    except Exception as e:
        logger.error(f"Error in show_payment_stats: {e}", exc_info=True)
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

        # ✅ ИСПРАВЛЕНО: Проверка что администратор ещё не добавлен через SQL
        db = get_db()
        query_check = "SELECT user_id FROM admins WHERE user_id = ?"
        existing = db.execute_query(query_check, (admin_id,))

        if existing:
            await message.answer(f"⚠️ Пользователь {admin_id} уже является администратором!")
            return

        # ✅ ИСПРАВЛЕНО: Добавляем администратора через SQL
        try:
            query_insert = """
                           INSERT INTO admins (user_id, is_active, created_at)
                           VALUES (?, 1, datetime('now')) \
                           """
            db.execute_insert(query_insert, (admin_id,))
            success = True
        except Exception as e:
            logger.error(f"Error adding admin: {e}", exc_info=True)
            success = False

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

    # ✅ ИСПРАВЛЕНО: Получаем список администраторов через SQL
    db = get_db()
    query = """
            SELECT user_id, username, full_name, created_at, is_active
            FROM admins
            WHERE is_active = 1
            ORDER BY created_at DESC \
            """
    admins = db.execute_query(query)

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

        # ✅ ИСПРАВЛЕНО: Проверка что это администратор через SQL
        db = get_db()
        query_check = "SELECT user_id FROM admins WHERE user_id = ?"
        existing = db.execute_query(query_check, (admin_id,))

        if not existing:
            await message.answer(f"⚠️ Пользователь {admin_id} не является администратором!")
            return

        # ✅ ИСПРАВЛЕНО: Удаляем администратора через SQL
        try:
            query_delete = "DELETE FROM admins WHERE user_id = ?"
            db.execute_update(query_delete, (admin_id,))
            success = True
        except Exception as e:
            logger.error(f"Error removing admin: {e}", exc_info=True)
            success = False

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

    # ✅ ИСПРАВЛЕНО: Получаем список администраторов через SQL
    db = get_db()
    query = """
            SELECT user_id, username, full_name, created_at, is_active
            FROM admins
            ORDER BY created_at DESC \
            """
    admins = db.execute_query(query)

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