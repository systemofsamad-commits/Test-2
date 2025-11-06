# from aiogram import Router
#
# from .admin import admin_router
# from .cmd_handlers import cmd_router
# from .user_handlers import user_router
#
#
# app_router = Router(name="app")
# app_router.include_router(cmd_router)
# app_router.include_router(user_router)
# app_router.include_router(admin_router)
#
# __all__ = ["app_router"]
from aiogram import Router

# Импортируем все роутеры
from .admin import admin_router
from .user_handlers import user_router  # ✅ РАСКОММЕНТИРОВАНО!

# Создаём главный роутер приложения
app_router = Router(name="app")

# ✅ ВАЖНО: Порядок имеет значение!
# Сначала пользовательские обработчики, потом админские
app_router.include_router(user_router)   # ✅ Пользовательские обработчики
app_router.include_router(admin_router)  # ✅ Админские обработчики

__all__ = ["app_router"]