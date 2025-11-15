import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from config import Config
from helpers import is_admin, get_db

logger = logging.getLogger(__name__)
router = Router(name="admin_status_handlers")
config = Config()


@router.callback_query(F.data.startswith("admin_quick_"))
async def quick_status_change(callback: CallbackQuery, state: FSMContext):
    """Быстрая смена статуса студента"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    try:
        callback_data = callback.data
        logger.info(f"Quick status change data: {callback_data}")

        # Убираем префикс "admin_quick_"
        data_without_prefix: str = callback_data.replace("admin_quick_", "")

        # Разделяем на части по последнему подчёркиванию
        last_underscore_index = data_without_prefix.rfind('_')
        if last_underscore_index == -1:
            await callback.answer("❌ Ошибка формата данных")
            return

        new_status = data_without_prefix[:last_underscore_index]
        registration_id_str = data_without_prefix[last_underscore_index + 1:]

        try:
            registration_id = int(registration_id_str)
        except ValueError:
            await callback.answer("❌ Неверный ID студента")
            return

        logger.info(f"Changing status for student {registration_id} to {new_status}")

        # ✅ ИСПРАВЛЕНО: Прямой SQL SELECT
        db = get_db()
        query = """
            SELECT r.id, r.status_code,
                   r.full_name as name, r.phone,
                   c.name as course_name
            FROM registrations r
            LEFT JOIN courses c ON r.course_id = c.id
            WHERE r.id = ?
        """
        results = db.execute_query(query, (registration_id,))
        reg = results[0] if results else None

        if not reg:
            await callback.answer("❌ Студент не найден")
            return

        # Сохраняем данные для подтверждения
        await state.update_data(
            registration_id=registration_id,
            new_status=new_status,
            student_name=reg['name'],
            current_status=reg['status_code']
        )

        status_names = {
            'trial': '🟡 Пробный урок',
            'studying': '🔵 Обучаются',
            'frozen': '⚪ Заморожены',
            'waiting_payment': '🟠 Ожидание оплаты',
            'completed': '🟣 Завершили',
            'active': '🟢 Активные'
        }

        current_status_name = config.STATUSES.get(reg['status_code'], reg['status_code'])
        new_status_name = status_names.get(new_status, new_status)

        # Показываем подтверждение
        from keyboards.admin_kb import get_status_change_confirmation_keyboard
        await callback.message.edit_text(
            f"🔄 *Смена статуса студента*\n\n"
            f"👤 *Студент:* {reg['name']}\n"
            f"📞 Телефон: {reg.get('phone', 'Не указан')}\n"
            f"📚 Курс: {reg.get('course_name', 'Не указан')}\n\n"
            f"📊 *Текущий статус:* {current_status_name}\n"
            f"🎯 *Новый статус:* {new_status_name}\n\n"
            f"✅ *Подтвердите изменение статуса:*",
            parse_mode="Markdown",
            reply_markup=get_status_change_confirmation_keyboard(registration_id, new_status)
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in quick_status_change: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("admin_confirm_"))
async def confirm_status_change(callback: CallbackQuery):
    """Подтверждение смены статуса"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    try:
        # Разбираем данные
        callback_data = callback.data
        logger.info(f"Confirm status change data: {callback_data}")

        # Убираем префикс "admin_confirm_"
        data_without_prefix = callback_data.replace("admin_confirm_", "")

        # Разделяем на части по последнему подчёркиванию
        last_underscore_index = data_without_prefix.rfind('_')
        if last_underscore_index == -1:
            await callback.answer("❌ Ошибка формата данных")
            return

        new_status = data_without_prefix[:last_underscore_index]
        registration_id_str = data_without_prefix[last_underscore_index + 1:]

        try:
            registration_id = int(registration_id_str)
        except ValueError:
            await callback.answer("❌ Неверный ID студента")
            return

        # ✅ ИСПРАВЛЕНО: Прямой SQL UPDATE
        db = get_db()
        try:
            query = """
                UPDATE registrations
                SET status_code = ?,
                    updated_at = datetime('now')
                WHERE id = ?
            """
            db.execute_update(query, (new_status, registration_id))
            success = True
        except Exception as e:
            logger.error(f"Error updating status: {e}", exc_info=True)
            success = False

        if success:
            # ✅ ИСПРАВЛЕНО: Прямой SQL SELECT для получения обновлённых данных
            query = """
                SELECT r.id, r.status_code,
                       r.full_name as name, r.phone,
                       c.name as course_name
                FROM registrations r
                LEFT JOIN courses c ON r.course_id = c.id
                WHERE r.id = ?
            """
            results = db.execute_query(query, (registration_id,))
            reg = results[0] if results else None

            if not reg:
                await callback.answer("❌ Студент не найден")
                return

            status_names = {
                'trial': '🟡 Пробный урок',
                'studying': '🔵 Обучаются',
                'frozen': '⚪ Заморожены',
                'waiting_payment': '🟠 Ожидание оплаты',
                'completed': '🟣 Завершили',
                'active': '🟢 Активные'
            }

            new_status_name = status_names.get(new_status, new_status)

            from keyboards.admin_kb import get_student_actions_keyboard
            await callback.message.edit_text(
                f"✅ *Статус успешно обновлён!*\n\n"
                f"👤 *Студент:* {reg['name']}\n"
                f"📞 Телефон: {reg.get('phone', 'Не указан')}\n"
                f"📚 Курс: {reg.get('course_name', 'Не указан')}\n\n"
                f"🎯 *Новый статус:* {new_status_name}\n\n"
                f"📊 Студент перемещён в соответствующую категорию.",
                parse_mode="Markdown",
                reply_markup=get_student_actions_keyboard(registration_id, new_status)
            )

            logger.info(f"✅ Статус студента {reg['name']} (ID: {registration_id}) изменён на {new_status}")

        else:
            # ✅ ИСПРАВЛЕНО: Прямой SQL SELECT
            query = """
                SELECT r.id, r.status_code,
                       r.full_name as name, r.phone,
                       c.name as course_name
                FROM registrations r
                LEFT JOIN courses c ON r.course_id = c.id
                WHERE r.id = ?
            """
            results = db.execute_query(query, (registration_id,))
            reg = results[0] if results else None

            if reg:
                from keyboards.admin_kb import get_student_actions_keyboard
                await callback.message.edit_text(
                    "❌ *Ошибка при обновлении статуса*\n\n"
                    "Попробуйте ещё раз или обратитесь к разработчику.",
                    parse_mode="Markdown",
                    reply_markup=get_student_actions_keyboard(registration_id, reg['status_code'])
                )

    except Exception as e:
        logger.error(f"Error in confirm_status_change: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("admin_cancel_"))
async def cancel_status_change(callback: CallbackQuery):
    """Отмена смены статуса"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    try:
        registration_id = int(callback.data.replace("admin_cancel_", ""))

        # ✅ ИСПРАВЛЕНО: Прямой SQL SELECT
        db = get_db()
        query = """
            SELECT r.id, r.status_code,
                   r.full_name as name, r.phone,
                   c.name as course_name
            FROM registrations r
            LEFT JOIN courses c ON r.course_id = c.id
            WHERE r.id = ?
        """
        results = db.execute_query(query, (registration_id,))
        reg = results[0] if results else None

        if reg:
            from keyboards.admin_kb import get_student_actions_keyboard
            await callback.message.edit_text(
                f"❌ *Смена статуса отменена*\n\n"
                f"👤 *Студент:* {reg['name']}\n"
                f"📊 Статус остался без изменений.",
                parse_mode="Markdown",
                reply_markup=get_student_actions_keyboard(registration_id, reg['status_code'])
            )
        else:
            await callback.answer("❌ Студент не найден")

    except Exception as e:
        logger.error(f"Error in cancel_status_change: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("admin_back_"))
async def back_to_student(callback: CallbackQuery):
    """Возврат к карточке студента"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    try:
        registration_id = int(callback.data.replace("admin_back_", ""))

        # ✅ ИСПРАВЛЕНО: Прямой SQL SELECT
        db = get_db()
        query = """
            SELECT r.id, r.status_code,
                   r.full_name as name, r.phone,
                   c.name as course_name
            FROM registrations r
            LEFT JOIN courses c ON r.course_id = c.id
            WHERE r.id = ?
        """
        results = db.execute_query(query, (registration_id,))
        reg = results[0] if results else None

        if reg:
            status_text = config.STATUSES.get(reg['status_code'], reg['status_code'])
            info_text = (
                f"📋 *Карточка студента:*\n\n"
                f"👤 Имя: {reg['name']}\n"
                f"📞 Телефон: {reg.get('phone', 'Не указан')}\n"
                f"🎯 Курс: {reg.get('course_name', 'Не указан')}\n"
                f"📊 Статус: {status_text}\n"
                f"🆔 ID: {reg['id']}\n"
            )

            from keyboards.admin_kb import get_student_actions_keyboard
            await callback.message.edit_text(
                info_text,
                parse_mode="Markdown",
                reply_markup=get_student_actions_keyboard(registration_id, reg['status_code'])
            )
        else:
            await callback.answer("❌ Студент не найден")

    except Exception as e:
        logger.error(f"Error in back_to_student: {e}", exc_info=True)
        await callback.answer("❌ Произошла ошибка")