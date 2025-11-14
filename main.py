import asyncio
import logging
import os
import sys

sys.path.append(os.path.dirname(__file__))

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from keyboards.user_kb import get_main_keyboard
from keyboards.admin_kb import get_admin_main_keyboard
from helpers import is_admin, get_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    config = Config()
    bot_instance = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # ✅ ИНИЦИАЛИЗАЦИЯ БД (упрощенная версия)
    try:
        # Получаем экземпляр БД (это автоматически инициализирует схему)
        db = get_db()

        # Проверяем структуру
        if db.check_database_structure():
            logger.info("✅ Database initialized successfully")
        else:
            logger.warning("⚠️ Database structure check failed")

    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}", exc_info=True)
        # Не прерываем запуск - БД может быть уже инициализирована
        logger.info("Continuing with existing database...")

    # ✅ КОМАНДА /start
    @dp.message(Command("start"))
    async def start_command(message: Message):
        """Обработчик команды /start"""
        try:
            await message.answer(
                "🎓 Добро пожаловать в образовательный центр!\n\n"
                "Выберите действие:",
                reply_markup=get_main_keyboard()
            )
            logger.info(f"User {message.from_user.id} started the bot")
        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await message.answer("Произошла ошибка. Попробуйте позже.")

    # ✅ КОМАНДА /admin
    @dp.message(Command("admin"))
    async def admin_command(message: Message):
        """Обработчик команды /admin"""
        try:
            if is_admin(message.from_user.id):
                await message.answer(
                    "📊 Панель администратора\n\n"
                    "Добро пожаловать в админ-панель!",
                    reply_markup=get_admin_main_keyboard()
                )
                logger.info(f"Admin {message.from_user.id} accessed admin panel")
            else:
                await message.answer("❌ У вас нет доступа к админ-панели")
                logger.warning(f"User {message.from_user.id} tried to access admin panel")
        except Exception as e:
            logger.error(f"Error in admin_command: {e}")
            await message.answer("Произошла ошибка. Попробуйте позже.")

    # Регистрация роутеров
    try:
        # Импортируем роутеры
        from handlers.admin import admin_router
        from handlers import app_router

        # ВАЖНО: Включаем ТОЛЬКО app_router, так как admin_router уже включён в него
        dp.include_router(app_router)

        logger.info("✅ Routers registered successfully")
        logger.info(f"  - App router includes: {[r.name for r in app_router.sub_routers]}")
    except Exception as e:
        logger.error(f"❌ Error registering routers: {e}", exc_info=True)
        return

    # ✅ ЗАПУСК БОТА
    try:
        logger.info("🚀 Bot starting...")
        logger.info(f"Bot token: {config.BOT_TOKEN[:10]}...")
        logger.info(f"Admin IDs: {config.ADMIN_IDS}")

        # Удаляем вебхук если был установлен
        await bot_instance.delete_webhook(drop_pending_updates=True)

        # Запускаем polling
        await dp.start_polling(
            bot_instance,
            allowed_updates=dp.resolve_used_update_types()
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
    finally:
        # Закрываем соединения
        await bot_instance.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")