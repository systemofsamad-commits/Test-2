import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

from config import Config
from database import Database
from helpers import is_admin

logger = logging.getLogger(__name__)
router = Router(name="admin_handlers_base")
config = Config()
db = Database(config.DB_NAME)


# ============ БАЗОВАЯ АДМИН-ПАНЕЛЬ ============

@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery):
    """Показать главное меню админ-панели"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    from keyboards.admin_kb import get_admin_main_keyboard
    await callback.message.edit_text(
        "📊 Панель администратора\n\n"
        "Выберите раздел для управления:",
        reply_markup=get_admin_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_admin_main")
async def back_to_admin_main(callback: CallbackQuery):
    """Возврат в главное меню админки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    from keyboards.admin_kb import get_admin_main_keyboard
    await callback.message.edit_text(
        "📊 Панель администратора",
        reply_markup=get_admin_main_keyboard()
    )
    await callback.answer()


# ============ МЕНЮ СТУДЕНТОВ ============

@router.callback_query(F.data == "admin_students_menu")
async def admin_students_menu(callback: CallbackQuery):
    """Меню управления студентами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return

    from keyboards.admin_kb import get_admin_students_menu
    await callback.message.edit_text(
        "👥 *Управление студентами*\n\n"
        "Выберите группу студентов или действие:",
        parse_mode="Markdown",
        reply_markup=get_admin_students_menu()
    )
    await callback.answer()


# ============ МЕНЮ ПРЕПОДАВАТЕЛЕЙ ============

@router.callback_query(F.data == "admin_teachers_menu")
async def admin_teachers_menu(callback: CallbackQuery):
    """Меню управления преподавателями"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return

    from keyboards.admin_kb import get_admin_teachers_menu
    await callback.message.edit_text(
        "👨‍🏫 *Управление преподавателями*",
        parse_mode="Markdown",
        reply_markup=get_admin_teachers_menu()
    )
    await callback.answer()


# ============ МЕНЮ КУРСОВ ============

@router.callback_query(F.data == "admin_courses_menu")
async def admin_courses_menu(callback: CallbackQuery):
    """Меню управления курсами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return

    from keyboards.admin_kb import get_admin_courses_menu
    await callback.message.edit_text(
        "📚 *Управление курсами*",
        parse_mode="Markdown",
        reply_markup=get_admin_courses_menu()
    )
    await callback.answer()


# ============ МЕНЮ АДМИНИСТРАТОРОВ ============

@router.callback_query(F.data == "admin_admins_menu")
async def admin_admins_menu(callback: CallbackQuery):
    """Меню управления администраторами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return

    admins = db.get_all_admins()

    if not admins:
        text = "📋 Список администраторов пуст"
    else:
        text = "📋 *Список администраторов:*\n\n"
        for admin in admins:
            text += f"👤 ID: `{admin['user_id']}`\n"
            if admin.get('username'):
                text += f"📱 @{admin['username']}\n"
            if admin.get('full_name'):
                text += f"📛 {admin['full_name']}\n"
            text += f"📅 Добавлен: {admin['created_at'][:10]}\n"
            text += f"🔹 Статус: {'Активен' if admin['is_active'] else 'Неактивен'}\n\n"

    from keyboards.admin_kb import get_admin_admins_menu
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_admin_admins_menu()
    )
    await callback.answer()


# ============ МЕНЮ СТАТИСТИКИ ============

@router.callback_query(F.data == "admin_stats_menu")
async def admin_stats_menu(callback: CallbackQuery):
    """Меню статистики"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return

    from keyboards.admin_kb import get_admin_stats_menu
    await callback.message.edit_text(
        "📊 *Статистика*\n\n"
        "Выберите раздел:",
        parse_mode="Markdown",
        reply_markup=get_admin_stats_menu()
    )
    await callback.answer()


# ============ УПРАВЛЕНИЕ ГРУППАМИ ============

@router.callback_query(F.data == "manage_groups")
async def manage_groups(callback: CallbackQuery):
    """Управление группами"""
    if not is_admin(callback.from_user.id):
        return

    from keyboards.admin_kb import get_group_management_keyboard
    await callback.message.edit_text(
        "👥 *Управление группами*",
        parse_mode="Markdown",
        reply_markup=get_group_management_keyboard()
    )
    await callback.answer()


# ============ УПРАВЛЕНИЕ УРОКАМИ ============

@router.callback_query(F.data == "manage_lessons")
async def manage_lessons(callback: CallbackQuery):
    """Управление уроками"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return

    from keyboards.admin_kb import get_lesson_management_keyboard
    await callback.message.edit_text(
        "📖 *Управление уроками*",
        parse_mode="Markdown",
        reply_markup=get_lesson_management_keyboard()
    )
    await callback.answer()


# ============ ВОЗВРАТ В ГЛАВНОЕ МЕНЮ ============

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Возврат в главное меню бота"""
    from keyboards.user_kb import get_main_keyboard
    await callback.message.edit_text(
        "🎓 Главное меню\n\n"
        "Выберите действие:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()