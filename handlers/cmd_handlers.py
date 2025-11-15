import os
import sys

# Добавляем путь к корневой папке проекта
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from aiogram import Router
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from keyboards.user_kb import get_main_keyboard
from helpers import is_admin

cmd_router = Router(name="cmd_router")


@cmd_router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Обработчик команды /admin"""
    from helpers import is_admin
    from keyboards.admin_kb import get_admin_main_keyboard  # ✅ ПРАВИЛЬНЫЙ ИМПОРТ

    if not is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return

    await message.answer(
        "📊 Администраторская панель\n\nВыберите категорию для управления:",
        reply_markup=get_admin_main_keyboard()  # ✅ ПРАВИЛЬНАЯ ФУНКЦИЯ
    )


@cmd_router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    from keyboards.user_kb import get_main_keyboard
    await message.answer(
        "🎓 Добро пожаловать в образовательный центр!",
        reply_markup=get_main_keyboard()
    )


@cmd_router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "📖 Помощь по боту:\n"
        "/start - начать работу\n"
        "/admin - админ-панель (только для администраторов)\n"
        "/help - показать это сообщение"
    )


async def start_command(message: Message, state: FSMContext):
    """Альтернативный обработчик команды /start"""
    await state.clear()
    await message.answer(
        "🎓 Добро пожаловать в учебный центр!\n\n"
        "Вы можете записаться на несколько курсов одновременно!\n\n"
        "• 📚 Курсы - посмотреть доступные курсы\n"
        "• 📝 Новая запись - записаться на новый курс\n"
        "• 👤 Мой кабинет - ваши текущие записи\n"
        "• ℹ️ О центре - информация о нас",
        reply_markup=get_main_keyboard()
    )


async def admin_panel(message: Message, state: FSMContext):
    """Альтернативный обработчик команды /admin"""
    if not is_admin(message.from_user.id):
        await message.answer("Команда не распознана. Используйте кнопки меню ниже 👇",
                             reply_markup=get_main_keyboard())
        return

    await state.clear()

    # ✅ ИСПРАВЛЕНО: Используем правильную функцию
    from keyboards.admin_kb import get_admin_main_keyboard
    await message.answer("Панель администратора", reply_markup=get_admin_main_keyboard())


def register_command_handlers(dp: Dispatcher):
    """Регистрация обработчиков команд (legacy)"""
    dp.message.register(start_command, Command("start"))
    dp.message.register(admin_panel, Command("admin"))