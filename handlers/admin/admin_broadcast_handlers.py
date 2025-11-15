import asyncio
import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Config
from helpers import is_admin, get_db
from states.admin_states import AdminStates

logger = logging.getLogger(__name__)
router = Router(name="admin_broadcast_handlers")
config = Config()


@router.callback_query(F.data == "start_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    """Начало рассылки"""
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.waiting_for_broadcast_group)
    from keyboards.admin_kb import get_broadcast_group_keyboard
    await callback.message.edit_text(
        "📢 *Рассылка сообщений*\n\n"
        "Выберите группу получателей:",
        parse_mode="Markdown",
        reply_markup=get_broadcast_group_keyboard()
    )


@router.callback_query(F.data.startswith("broadcast_"), AdminStates.waiting_for_broadcast_group)
async def choose_broadcast_group(callback: CallbackQuery, state: FSMContext):
    """Выбор группы для рассылки"""
    if not is_admin(callback.from_user.id):
        return

    group = callback.data.replace("broadcast_", "")
    await state.update_data(broadcast_group=group)
    await state.set_state(AdminStates.waiting_for_broadcast_text)

    from keyboards.admin_kb import get_cancel_keyboard
    await callback.message.edit_text(
        f"📢 Рассылка для группы: *{group}*\n\n"
        "Введите текст сообщения:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_broadcast_text)
async def process_broadcast_text(message: Message, state: FSMContext):
    """Обработка текста рассылки"""
    if not is_admin(message.from_user.id):
        return

    if message.text in ["❌ Отмена", "◀️ Назад"]:
        await state.clear()
        from keyboards.admin_kb import get_admin_main_keyboard
        await message.answer("❌ Рассылка отменена.", reply_markup=get_admin_main_keyboard())
        return

    data = await state.get_data()
    group = data.get('broadcast_group')
    broadcast_text = message.text

    db = get_db()
    recipients = []

    if group == "all":
        # ✅ ИСПРАВЛЕНО: Прямой SQL запрос для получения всех пользователей
        query = """
            SELECT DISTINCT u.telegram_id, u.full_name
            FROM registrations r
            JOIN users u ON r.user_id = u.id
            WHERE u.telegram_id IS NOT NULL
        """
        users = db.execute_query(query)
        recipients = [{'telegram_id': u['telegram_id'], 'name': u.get('full_name', 'Пользователь')} for u in users]
    else:
        # Ищем статус по названию
        status = None
        for key, value in config.STATUSES.items():
            if value == group:
                status = key
                break

        if status:
            # ✅ ИСПРАВЛЕНО: Прямой SQL запрос с JOIN
            query = """
                SELECT r.*, u.telegram_id, u.full_name as name
                FROM registrations r
                JOIN users u ON r.user_id = u.id
                WHERE r.status_code = ? AND u.telegram_id IS NOT NULL
            """
            registrations = db.execute_query(query, (status,))
            recipients = [{'telegram_id': r['telegram_id'], 'name': r['name']} for r in registrations if
                          r.get('telegram_id')]

    if not recipients:
        from keyboards.admin_kb import get_admin_main_keyboard
        await message.answer(
            "❌ Нет студентов в выбранной группе.",
            reply_markup=get_admin_main_keyboard()
        )
        await state.clear()
        return

    from keyboards.admin_kb import get_admin_main_keyboard
    await message.answer(
        f"📤 Начинаю рассылку для {len(recipients)} студентов...",
        reply_markup=get_admin_main_keyboard()
    )

    success_count = 0
    fail_count = 0

    for recipient in recipients:
        try:
            telegram_id = recipient['telegram_id']
            await message.bot.send_message(telegram_id, f"📢 {broadcast_text}")
            success_count += 1
            await asyncio.sleep(0.05)  # Задержка между сообщениями
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения пользователю {recipient.get('name', 'Unknown')}: {e}")
            fail_count += 1

    report_text = (
        f"✅ *Рассылка завершена!*\n\n"
        f"✅ Успешно отправлено: {success_count}\n"
        f"❌ Не отправлено: {fail_count}\n"
    )

    await message.answer(report_text, parse_mode="Markdown", reply_markup=get_admin_main_keyboard())
    await state.clear()