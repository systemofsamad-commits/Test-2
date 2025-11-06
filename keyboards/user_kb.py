from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

config = Config()


# ============ ГЛАВНОЕ МЕНЮ ============

def get_main_keyboard():
    """Главное меню пользователя - компактное"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Новая запись", callback_data="new_registration")],
        [
            InlineKeyboardButton(text="👤 Мой кабинет", callback_data="my_cabinet"),
            InlineKeyboardButton(text="📚 Курсы", callback_data="show_courses")
        ],
        [
            InlineKeyboardButton(text="ℹ️ О центре", callback_data="about_center"),
            InlineKeyboardButton(text="💬 Отзыв", callback_data="leave_feedback")
        ]
    ])
    return keyboard


# ============ УНИВЕРСАЛЬНЫЕ ============

def get_cancel_keyboard():
    """Клавиатура отмены"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
    return keyboard


def get_back_keyboard(callback_data: str, text: str = "◀️ Назад"):
    """Универсальная клавиатура возврата"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data=callback_data)]
    ])
    return keyboard


def get_yes_no_keyboard(yes_callback: str, no_callback: str):
    """Универсальная клавиатура Да/Нет"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=yes_callback),
            InlineKeyboardButton(text="❌ Нет", callback_data=no_callback)
        ]
    ])
    return keyboard


def get_confirmation_keyboard():
    """Клавиатура подтверждения данных"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Всё верно", callback_data="confirm_registration"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data="new_registration")
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
    return keyboard


def get_courses_keyboard():
    buttons = []
    courses_list = list(config.COURSES.keys())
    for idx, course in enumerate(courses_list):
        buttons.append([InlineKeyboardButton(text=course, callback_data=f"course_{idx}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_training_types_keyboard(course_idx: int):
    """Клавиатура выбора типа обучения"""
    courses_list = list(config.COURSES.keys())
    course = courses_list[course_idx]
    training_types = list(config.COURSES[course].keys())

    buttons = []
    for idx, training_type in enumerate(training_types):
        price = config.COURSES[course][training_type]
        button_text = f"{training_type}\n💰 {price}"

        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"type_{course_idx}_{idx}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="new_registration")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_schedule_keyboard():
    """Клавиатура выбора расписания - компактная"""
    buttons = []

    # Расписания по 1 в ряд
    for idx, schedule in enumerate(config.SCHEDULES):
        buttons.append([InlineKeyboardButton(
            text=schedule,
            callback_data=f"schedule_{idx}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="new_registration")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============ ЛИЧНЫЙ КАБИНЕТ ============

def get_cabinet_keyboard():
    """Меню личного кабинета - улучшенное"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_registrations")],
        [
            InlineKeyboardButton(text="📚 Материалы", callback_data="my_materials"),
            InlineKeyboardButton(text="📊 Прогресс", callback_data="my_progress")
        ],
        [
            InlineKeyboardButton(text="🎯 Тесты", callback_data="take_quiz"),
            InlineKeyboardButton(text="📅 Расписание", callback_data="my_schedule")
        ],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main")]
    ])
    return keyboard


def get_registrations_keyboard(registrations: list):
    """Клавиатура со списком регистраций"""
    buttons = []

    if not registrations:
        buttons.append([InlineKeyboardButton(
            text="📝 Записаться на курс",
            callback_data="new_registration"
        )])
    else:
        # Регистрации по 1 в ряд
        for reg in registrations:
            status_emoji = {
                'active': '🟢',
                'trial': '🟡',
                'studying': '🔵',
                'frozen': '⚪',
                'waiting_payment': '🟠',
                'completed': '🟣'
            }.get(reg.status, '⚫')

            button_text = f"{status_emoji} {reg.course} - {config.STATUSES.get(reg.status, reg.status)}"

            buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"registration_detail_{reg.id}"
            )])

        # Кнопка новой записи
        buttons.append([InlineKeyboardButton(
            text="➕ Новая запись",
            callback_data="new_registration"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="my_cabinet")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_registration_detail_keyboard(registration_id: int):
    """Клавиатура детальной информации о регистрации"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📚 Материалы", callback_data=f"reg_materials_{registration_id}"),
            InlineKeyboardButton(text="🎯 Тесты", callback_data=f"reg_quiz_{registration_id}")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="my_registrations")]
    ])
    return keyboard


# ============ МАТЕРИАЛЫ ============

def get_materials_keyboard(course: str):
    """Клавиатура материалов курса"""
    buttons = []

    if course in config.MATERIALS:
        materials = config.MATERIALS[course]

        # Материалы по 1 в ряд
        for title, url in materials.items():
            buttons.append([InlineKeyboardButton(
                text=title,
                url=url
            )])

    buttons.extend([
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="my_materials")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="my_cabinet")]
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============ ТЕСТЫ/ВИКТОРИНЫ ============

def get_quiz_keyboard(course: str):
    """Клавиатура выбора теста"""
    buttons = []

    if course in config.QUIZZES:
        quizzes = config.QUIZZES[course]

        # Тесты по номерам
        for idx in range(len(quizzes)):
            buttons.append([InlineKeyboardButton(
                text=f"📝 Вопрос {idx + 1}",
                callback_data=f"quiz_{course}_{idx}"
            )])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="my_cabinet")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_quiz_answer_keyboard(course: str, question_idx: int, options: list):
    """Клавиатура ответов на вопрос теста"""
    buttons = []

    # Варианты ответов
    for idx, option in enumerate(options):
        buttons.append([InlineKeyboardButton(
            text=f"{chr(65 + idx)}. {option}",
            callback_data=f"quiz_answer_{course}_{question_idx}_{idx}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="take_quiz")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_quiz_results_keyboard():
    """Клавиатура результатов теста"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Пройти снова", callback_data="take_quiz"),
            InlineKeyboardButton(text="📚 Материалы", callback_data="my_materials")
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
    ])
    return keyboard


# ============ ОБРАТНАЯ СВЯЗЬ ============

def get_feedback_types_keyboard():
    """Клавиатура типов обратной связи"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Оставить отзыв", callback_data="feedback_review")],
        [InlineKeyboardButton(text="💡 Предложение", callback_data="feedback_suggestion")],
        [InlineKeyboardButton(text="🐞 Сообщить о проблеме", callback_data="feedback_issue")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")]
    ])
    return keyboard


def get_rating_keyboard():
    """Клавиатура выбора оценки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐", callback_data="rating_1"),
            InlineKeyboardButton(text="⭐⭐", callback_data="rating_2"),
            InlineKeyboardButton(text="⭐⭐⭐", callback_data="rating_3")
        ],
        [
            InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data="rating_4"),
            InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data="rating_5")
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
    return keyboard


def get_feedback_confirmation_keyboard():
    """Клавиатура подтверждения отзыва"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="feedback_send"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data="feedback_edit")
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
    return keyboard


def get_reminders_keyboard():
    """Клавиатура для управления напоминаниями"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить напоминание", callback_data="add_reminder")],
        [InlineKeyboardButton(text="📋 Мои напоминания", callback_data="show_reminders")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="show_cabinet")]
    ])
    return keyboard


# ============ ПРОГРЕСС ============

def get_progress_keyboard():
    """Клавиатура просмотра прогресса"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="progress_stats"),
            InlineKeyboardButton(text="📈 График", callback_data="progress_chart")
        ],
        [
            InlineKeyboardButton(text="🎯 Достижения", callback_data="progress_achievements"),
            InlineKeyboardButton(text="📅 История", callback_data="progress_history")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="my_cabinet")]
    ])
    return keyboard


def get_admin_keyboard():
    """Клавиатура для администратора"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Управление записями", callback_data="admin_registrations")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")]
    ])
    return keyboard

# ============ ЭКСПОРТ ============

__all__ = [
    'get_main_keyboard',
    'get_courses_keyboard',
    'get_training_types_keyboard',
    'get_schedule_keyboard',
    'get_confirmation_keyboard',
    'get_cabinet_keyboard',
    'get_registrations_keyboard',
    'get_registration_detail_keyboard',
    'get_materials_keyboard',
    'get_quiz_keyboard',
    'get_quiz_answer_keyboard',
    'get_quiz_results_keyboard',
    'get_feedback_types_keyboard',
    'get_rating_keyboard',
    'get_feedback_confirmation_keyboard',
    'get_progress_keyboard',
    'get_cancel_keyboard',
    'get_back_keyboard',
    'get_yes_no_keyboard',
]
