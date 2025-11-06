from .user_kb import (
    get_main_keyboard,
    get_cancel_keyboard,
    get_confirmation_keyboard,
    get_courses_keyboard,
    get_training_types_keyboard,
    get_schedule_keyboard,
    get_cabinet_keyboard,
    get_rating_keyboard,
    get_materials_keyboard,
    get_quiz_keyboard,
    get_quiz_results_keyboard,
    get_feedback_types_keyboard,  # ← БЫЛО: get_feedback_keyboard
    get_feedback_confirmation_keyboard,  # ← ДОБАВЛЕНО
    get_reminders_keyboard,
    get_progress_keyboard,
    get_registrations_keyboard,  # ← ДОБАВЛЕНО
    get_registration_detail_keyboard,  # ← ДОБАВЛЕНО
    get_back_keyboard,  # ← ДОБАВЛЕНО
    get_yes_no_keyboard,  # ← ДОБАВЛЕНО
)
from .admin_kb import (
    get_admin_main_keyboard,  # ← БЫЛО: get_admin_keyboard
    get_broadcast_group_keyboard,
    get_student_actions_keyboard
)

__all__ = [
    # User keyboards
    'get_main_keyboard',
    'get_cancel_keyboard',
    'get_confirmation_keyboard',
    'get_courses_keyboard',
    'get_training_types_keyboard',
    'get_schedule_keyboard',
    'get_cabinet_keyboard',
    'get_rating_keyboard',
    'get_materials_keyboard',
    'get_quiz_keyboard',
    'get_quiz_results_keyboard',
    'get_feedback_types_keyboard',
    'get_feedback_confirmation_keyboard',
    'get_reminders_keyboard',
    'get_progress_keyboard',
    'get_registrations_keyboard',
    'get_registration_detail_keyboard',
    'get_back_keyboard',
    'get_yes_no_keyboard',

    # Admin keyboards
    'get_admin_main_keyboard',
    'get_broadcast_group_keyboard',
    'get_student_actions_keyboard'
]