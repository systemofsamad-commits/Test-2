from aiogram import Router

# Импортируем все под-роутеры админки
from .admin_broadcast_handlers import router as broadcast_router
from .admin_handlers_base import router as base_router
from .admin_lesson_handlers import router as lesson_router
from .admin_management_handlers import router as management_router
from .admin_progress_handlers import router as progress_router
from .admin_status_handlers import router as status_router
from .admin_student_handlers import router as student_router
from .admin_stats_and_admins_handlers import router as stats_admins_router

# Создаём главный роутер админки
admin_router = Router(name="admin")

# Включаем все под-роутеры в правильном порядке
# ВАЖНО: Порядок имеет значение - более специфичные обработчики должны быть первыми
admin_router.include_router(base_router)  # Базовые обработчики (меню)
admin_router.include_router(status_router)  # Смена статусов
admin_router.include_router(student_router)  # Управление студентами
admin_router.include_router(progress_router)  # Прогресс
admin_router.include_router(lesson_router)  # Уроки
admin_router.include_router(management_router)  # Управление (учителя, курсы, группы)
admin_router.include_router(broadcast_router)  # Рассылка
admin_router.include_router(stats_admins_router)

__all__ = ["admin_router"]
