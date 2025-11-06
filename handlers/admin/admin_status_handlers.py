import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.admin_states import AdminStates
from database import Database
from helpers import is_admin
from config import Config

logger = logging.getLogger(__name__)
router = Router(name="admin_student_handlers")
config = Config()
db = Database(config.DB_NAME)


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
        data_without_prefix = callback_data.replace("admin_quick_", "")

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

        # Получаем информацию о студенте
        student = db.get_student_by_id(registration_id)
        if not student:
            await callback.answer("❌ Студент не найден")
            return

        # Сохраняем данные для подтверждения
        await state.update_data(
            registration_id=registration_id,
            new_status=new_status,
            student_name=student.name,
            current_status=student.status
        )

        status_names = {
            'trial': '🟡 Пробный урок',
            'studying': '🔵 Обучаются',
            'frozen': '⚪ Заморожены',
            'waiting_payment': '🟠 Ожидание оплаты',
            'completed': '🟣 Завершили',
            'active': '🟢 Активные'
        }

        current_status_name = config.STATUSES.get(student.status, student.status)
        new_status_name = status_names.get(new_status, new_status)

        # Показываем подтверждение
        from keyboards.admin_kb import get_status_change_confirmation_keyboard
        await callback.message.edit_text(
            f"🔄 *Смена статуса студента*\n\n"
            f"👤 *Студент:* {student.name}\n"
            f"📞 Телефон: {student.phone}\n"
            f"📚 Курс: {student.course}\n\n"
            f"📊 *Текущий статус:* {current_status_name}\n"
            f"🎯 *Новый статус:* {new_status_name}\n\n"
            f"✅ *Подтвердите изменение статуса:*",
            parse_mode="Markdown",
            reply_markup=get_status_change_confirmation_keyboard(registration_id, new_status, student.status)
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in quick_status_change: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("admin_confirm_"))
async def confirm_status_change(callback: CallbackQuery, state: FSMContext):
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

        # Обновляем статус в базе данных
        success = db.update_status(registration_id, new_status)

        if success:
            # Получаем обновлённые данные студента
            student = db.get_student_by_id(registration_id)

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
                f"👤 *Студент:* {student.name}\n"
                f"📞 Телефон: {student.phone}\n"
                f"📚 Курс: {student.course}\n\n"
                f"🎯 *Новый статус:* {new_status_name}\n\n"
                f"📊 Студент перемещён в соответствующую категорию.",
                parse_mode="Markdown",
                reply_markup=get_student_actions_keyboard(registration_id, new_status, student.name)
            )

            logger.info(f"✅ Статус студента {student.name} (ID: {registration_id}) изменён на {new_status}")

        else:
            student = db.get_student_by_id(registration_id)
            from keyboards.admin_kb import get_student_actions_keyboard
            await callback.message.edit_text(
                "❌ *Ошибка при обновлении статуса*\n\n"
                "Попробуйте ещё раз или обратитесь к разработчику.",
                parse_mode="Markdown",
                reply_markup=get_student_actions_keyboard(registration_id, student.status, student.name)
            )

    except Exception as e:
        logger.error(f"Error in confirm_status_change: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("admin_cancel_"))
async def cancel_status_change(callback: CallbackQuery):
    """Отмена смены статуса"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    try:
        registration_id = int(callback.data.replace("admin_cancel_", ""))
        student = db.get_student_by_id(registration_id)

        if student:
            from keyboards.admin_kb import get_student_actions_keyboard
            await callback.message.edit_text(
                f"❌ *Смена статуса отменена*\n\n"
                f"👤 *Студент:* {student.name}\n"
                f"📊 Статус остался без изменений.",
                parse_mode="Markdown",
                reply_markup=get_student_actions_keyboard(registration_id, student.status, student.name)
            )
        else:
            await callback.answer("❌ Студент не найден")

    except Exception as e:
        logger.error(f"Error in cancel_status_change: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith("admin_back_"))
async def back_to_student(callback: CallbackQuery):
    """Возврат к карточке студента"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    try:
        registration_id = int(callback.data.replace("admin_back_", ""))
        student = db.get_student_by_id(registration_id)

        if student:
            status_text = config.STATUSES.get(student.status, student.status)
            info_text = (
                f"📋 *Карточка студента:*\n\n"
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
            await callback.message.edit_text(
                info_text,
                parse_mode="Markdown",
                reply_markup=get_student_actions_keyboard(registration_id, student.status, student.name)
            )
        else:
            await callback.answer("❌ Студент не найден")

    except Exception as e:
        logger.error(f"Error in back_to_student: {e}")
        await callback.answer("❌ Произошла ошибка")