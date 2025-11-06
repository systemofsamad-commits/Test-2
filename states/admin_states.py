from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    # Основные состояния для работы со студентами
    waiting_for_student_id = State()
    waiting_for_student_phone = State()
    waiting_for_trial_time = State()
    waiting_for_lesson_time = State()

    # Состояния для рассылки
    waiting_for_broadcast_group = State()
    waiting_for_broadcast_text = State()

    # Состояния для управления администраторами
    waiting_for_admin_id = State()
    waiting_for_remove_admin_id = State()

    # Состояния для управления преподавателями
    waiting_for_teacher_name = State()
    waiting_for_teacher_phone = State()
    waiting_for_teacher_email = State()
    waiting_for_teacher_specialization = State()
    waiting_for_teacher_experience = State()

    # Состояния для управления группами
    waiting_for_group_name = State()
    waiting_for_group_course = State()
    waiting_for_group_teacher = State()
    waiting_for_group_schedule = State()
    waiting_for_group_max_students = State()

    # Состояния для управления курсами
    waiting_for_course_name = State()
    waiting_for_course_description = State()
    waiting_for_course_duration = State()
    waiting_for_course_price = State()

    # Состояния для управления студентами
    waiting_for_student_group = State()

    # Состояния для управления уроками
    waiting_for_lesson_group = State()
    waiting_for_lesson_topic = State()
    waiting_for_lesson_date = State()

    # Дополнительные состояния для подтверждения удаления (если нужно)
    waiting_for_remove_confirmation = State()