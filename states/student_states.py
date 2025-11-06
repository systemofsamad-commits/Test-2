from aiogram.fsm.state import State, StatesGroup


class StudentStates(StatesGroup):
    """Состояния для студентов"""

    # Регистрация
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_course = State()
    waiting_for_training_type = State()
    waiting_for_schedule = State()
    waiting_for_price = State()
    waiting_for_confirmation = State()

    # Пробный урок
    waiting_trial_date = State()
    waiting_for_trial_time = State()

    # Обновление прогресса
    waiting_custom_progress = State()
    waiting_for_progress_update = State()

    # Обратная связь
    waiting_for_feedback = State()
    waiting_for_rating = State()
    waiting_for_comment = State()

    # Дополнительная информация
    waiting_for_additional_info = State()
    waiting_for_notes = State()