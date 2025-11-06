from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    choosing_course = State()
    choosing_training_type = State()
    choosing_schedule = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    confirmation = State()


class FeedbackStates(StatesGroup):
    waiting_for_feedback_text = State()
    waiting_for_rating = State()
