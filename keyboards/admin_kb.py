from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

config = Config()

# Константы для отображения статусов
STATUS_DISPLAY_NAMES = {
    'active': '🟢 Активные',
    'trial': '🟡 Пробный урок',
    'studying': '🔵 Обучаются',
    'frozen': '⚪ Заморожены',
    'waiting_payment': '🟠 Ожидание оплаты',
    'completed': '🟣 Завершили'
}


# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============

def _create_back_button(callback_data: str, text: str = "◀️ Назад"):
    """Создать кнопку назад"""
    return [InlineKeyboardButton(text=text, callback_data=callback_data)]


def _create_two_column_buttons(buttons_data: list) -> list:
    """Распределить кнопки по 2 в ряд"""
    result = []
    for i in range(0, len(buttons_data), 2):
        row = []
        for j in range(2):
            if i + j < len(buttons_data):
                text, callback = buttons_data[i + j]
                row.append(InlineKeyboardButton(text=text, callback_data=callback))
        result.append(row)
    return result


# ============ ГЛАВНОЕ МЕНЮ ============

def get_admin_main_keyboard():
    """Главное меню админ-панели - компактное"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        # Управление людьми
        [
            InlineKeyboardButton(text="👥 Студенты", callback_data="admin_students_menu"),
            InlineKeyboardButton(text="👨‍🏫 Преподаватели", callback_data="admin_teachers_menu")
        ],
        # Управление обучением
        [
            InlineKeyboardButton(text="📚 Курсы", callback_data="admin_courses_menu"),
            InlineKeyboardButton(text="👥 Группы", callback_data="manage_groups")
        ],
        # Уроки и статистика
        [
            InlineKeyboardButton(text="📖 Уроки", callback_data="manage_lessons"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats_menu")
        ],
        # Система
        [
            InlineKeyboardButton(text="👤 Администраторы", callback_data="admin_admins_menu"),
            InlineKeyboardButton(text="📢 Рассылка", callback_data="start_broadcast")
        ],
        # Выход
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")]
    ])
    return keyboard


# ============ МЕНЮ СТУДЕНТОВ ============

def get_admin_students_menu():
    """Меню управления студентами - улучшенное"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        # Статусы в 2 колонки
        [
            InlineKeyboardButton(text="🟢 Активные", callback_data="view_students_active"),
            InlineKeyboardButton(text="🟡 Пробный урок", callback_data="view_students_trial")
        ],
        [
            InlineKeyboardButton(text="🔵 Обучаются", callback_data="view_students_studying"),
            InlineKeyboardButton(text="⚪ Заморожены", callback_data="view_students_frozen")
        ],
        [
            InlineKeyboardButton(text="🟠 Ожидание оплаты", callback_data="view_students_payment"),
            InlineKeyboardButton(text="🟣 Завершили", callback_data="view_students_completed")
        ],
        # Поиск
        [
            InlineKeyboardButton(text="🔍 По ID", callback_data="find_student_by_id"),
            InlineKeyboardButton(text="📞 По телефону", callback_data="find_student_by_phone")
        ],
        # Назад
        [_create_back_button("back_to_admin_main")[0]]
    ])
    return keyboard


def get_student_actions_keyboard(registration_id: int, current_status: str, student_name: str = ""):
    """Меню действий со студентом - улучшенное"""
    buttons = []

    # Быстрая смена статуса - только доступные переходы
    status_transitions = {
        'active': [('trial', '🟡 → Пробный'), ('studying', '🔵 → Обучение')],
        'trial': [('studying', '🔵 → Обучение'), ('active', '🟢 → Активный')],
        'studying': [('frozen', '⚪ → Заморозить'), ('completed', '🟣 → Завершить')],
        'frozen': [('studying', '🔵 → Возобновить')],
        'waiting_payment': [('studying', '🔵 → Оплачено')],
        'completed': []
    }

    # Добавляем кнопки смены статуса
    available_transitions = status_transitions.get(current_status, [])
    if available_transitions:
        status_buttons = []
        for new_status, button_text in available_transitions:
            status_buttons.append(InlineKeyboardButton(
                text=button_text,
                callback_data=f"admin_quick_{new_status}_{registration_id}"
            ))

        # Распределяем по 2 в ряд
        for i in range(0, len(status_buttons), 2):
            buttons.append(status_buttons[i:i + 2])

    # Дополнительные действия
    buttons.extend([
        [
            InlineKeyboardButton(text="📅 Пробный урок", callback_data=f"schedule_trial_{registration_id}"),
            InlineKeyboardButton(text="📊 Прогресс", callback_data=f"update_progress_{registration_id}")
        ],
        [
            InlineKeyboardButton(text="📞 Контакты", callback_data=f"student_contacts_{registration_id}"),
            InlineKeyboardButton(text="📋 Подробнее", callback_data=f"full_info_{registration_id}")
        ],
        [_create_back_button("admin_students_menu")[0]]
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============ ПОДТВЕРЖДЕНИЯ ============

def get_status_change_confirmation_keyboard(registration_id: int, new_status: str, old_status: str):
    """Клавиатура подтверждения смены статуса"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, изменить", callback_data=f"admin_confirm_{new_status}_{registration_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin_cancel_{registration_id}")
        ]
    ])
    return keyboard


def get_confirmation_keyboard(confirm_callback: str, cancel_callback: str = "cancel"):
    """Универсальная клавиатура подтверждения"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=confirm_callback),
            InlineKeyboardButton(text="❌ Отмена", callback_data=cancel_callback)
        ]
    ])
    return keyboard


# ============ ПРЕПОДАВАТЕЛИ ============

def get_admin_teachers_menu():
    """Меню управления преподавателями"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список преподавателей", callback_data="list_teachers")],
        [
            InlineKeyboardButton(text="➕ Добавить", callback_data="add_teacher"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_teacher")
        ],
        [_create_back_button("back_to_admin_main")[0]]
    ])
    return keyboard


# ============ КУРСЫ ============

def get_admin_courses_menu():
    """Меню управления курсами"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список курсов", callback_data="list_courses")],
        [
            InlineKeyboardButton(text="➕ Добавить", callback_data="add_course"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_course")
        ],
        [_create_back_button("back_to_admin_main")[0]]
    ])
    return keyboard


# ============ ГРУППЫ ============

def get_group_management_keyboard():
    """Меню управления группами"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список групп", callback_data="list_groups")],
        [
            InlineKeyboardButton(text="➕ Добавить", callback_data="add_group"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_group")
        ],
        [_create_back_button("back_to_admin_main")[0]]
    ])
    return keyboard


# ============ УРОКИ ============

def get_lesson_management_keyboard():
    """Меню управления уроками"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список уроков", callback_data="list_lessons")],
        [
            InlineKeyboardButton(text="➕ Добавить урок", callback_data="add_lesson"),
            InlineKeyboardButton(text="📅 Расписание", callback_data="view_schedule")
        ],
        [_create_back_button("back_to_admin_main")[0]]
    ])
    return keyboard


# ============ АДМИНИСТРАТОРЫ ============

def get_admin_admins_menu():
    """Меню управления администраторами - компактное"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список администраторов", callback_data="list_admins")],
        [
            InlineKeyboardButton(text="➕ Добавить", callback_data="add_admin"),
            InlineKeyboardButton(text="➖ Удалить", callback_data="remove_admin")
        ],
        [_create_back_button("back_to_admin_main")[0]]
    ])
    return keyboard


# ============ СТАТИСТИКА ============

def get_admin_stats_menu():
    """Меню статистики - компактное"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Общая", callback_data="show_general_stats"),
            InlineKeyboardButton(text="📅 За неделю", callback_data="show_weekly_stats")
        ],
        [
            InlineKeyboardButton(text="💬 Отзывы", callback_data="show_feedback_stats"),
            InlineKeyboardButton(text="💰 Оплаты", callback_data="show_payment_stats")
        ],
        [_create_back_button("back_to_admin_main")[0]]
    ])
    return keyboard


# ============ РАССЫЛКА ============

def get_broadcast_group_keyboard():
    """Клавиатура выбора группы для рассылки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Всем студентам", callback_data="broadcast_all")],
        [
            InlineKeyboardButton(text="🟢 Активным", callback_data="broadcast_Активные"),
            InlineKeyboardButton(text="🔵 Обучающимся", callback_data="broadcast_Обучаются")
        ],
        [
            InlineKeyboardButton(text="🟡 Пробный урок", callback_data="broadcast_Пробный урок"),
            InlineKeyboardButton(text="⚪ Замороженным", callback_data="broadcast_Заморожены")
        ],
        [_create_back_button("back_to_admin_main", "❌ Отмена")[0]]
    ])
    return keyboard


# ============ ОТМЕНА ============

def get_cancel_keyboard():
    """Клавиатура отмены"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
    return keyboard

def get_cancel_and_back_keyboard(back_callback: str):
    """Клавиатура с отменой и возвратом"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
            InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)
        ]
    ])
    return keyboard


# ============ НАВИГАЦИЯ ============

def get_pagination_keyboard(
        current_page: int,
        total_pages: int,
        callback_prefix: str,
        back_callback: str = "back_to_admin_main"
):
    """Клавиатура с пагинацией"""
    buttons = []

    # Навигация по страницам
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton(
            text="⬅️",
            callback_data=f"{callback_prefix}_page_{current_page - 1}"
        ))

    nav_buttons.append(InlineKeyboardButton(
        text=f"📄 {current_page}/{total_pages}",
        callback_data="noop"
    ))

    if current_page < total_pages:
        nav_buttons.append(InlineKeyboardButton(
            text="➡️",
            callback_data=f"{callback_prefix}_page_{current_page + 1}"
        ))

    buttons.append(nav_buttons)
    buttons.append([_create_back_button(back_callback)[0]])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============ СПИСКИ С ДЕЙСТВИЯМИ ============

def get_teacher_list_keyboard(teachers: list, back_callback: str = "admin_teachers_menu"):
    """Клавиатура со списком преподавателей для выбора"""
    buttons = []

    # Преподаватели по 1 в ряд
    for teacher in teachers:
        buttons.append([InlineKeyboardButton(
            text=f"👨‍🏫 {teacher['name']}",
            callback_data=f"teacher_detail_{teacher['id']}"
        )])

    # Кнопки управления
    buttons.extend([
        [InlineKeyboardButton(text="➕ Добавить преподавателя", callback_data="add_teacher")],
        [_create_back_button(back_callback)[0]]
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_course_list_keyboard(courses: list, back_callback: str = "admin_courses_menu"):
    """Клавиатура со списком курсов для выбора"""
    buttons = []

    # Курсы по 1 в ряд
    for course in courses:
        buttons.append([InlineKeyboardButton(
            text=f"📚 {course['name']}",
            callback_data=f"course_detail_{course['id']}"
        )])

    # Кнопки управления
    buttons.extend([
        [InlineKeyboardButton(text="➕ Добавить курс", callback_data="add_course")],
        [_create_back_button(back_callback)[0]]
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_group_list_keyboard(groups: list, back_callback: str = "manage_groups"):
    """Клавиатура со списком групп для выбора"""
    buttons = []

    # Группы по 1 в ряд с доп. информацией
    for group in groups:
        teacher_name = group.get('teacher_name', 'Без преподавателя')
        student_count = group.get('current_students', 0)
        max_students = group.get('max_students', 0)

        button_text = f"👥 {group['name']} ({student_count}/{max_students}) - {teacher_name}"
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"group_detail_{group['id']}"
        )])

    # Кнопки управления
    buttons.extend([
        [InlineKeyboardButton(text="➕ Добавить группу", callback_data="add_group")],
        [_create_back_button(back_callback)[0]]
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ============ ЭКСПОРТ ============

__all__ = [
    'get_admin_main_keyboard',
    'get_admin_students_menu',
    'get_admin_teachers_menu',
    'get_admin_courses_menu',
    'get_admin_stats_menu',
    'get_admin_admins_menu',
    'get_group_management_keyboard',
    'get_lesson_management_keyboard',
    'get_broadcast_group_keyboard',
    'get_cancel_keyboard',
    'get_cancel_and_back_keyboard',
    'get_student_actions_keyboard',
    'get_status_change_confirmation_keyboard',
    'get_confirmation_keyboard',
    'get_progress_update_keyboard',
    'get_pagination_keyboard',
    'get_teacher_list_keyboard',
    'get_course_list_keyboard',
    'get_group_list_keyboard',
]

# ============ ПРОГРЕСС ============

def get_progress_update_keyboard(registration_id: int):
    """Клавиатура обновления прогресса - компактная"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐ Отлично", callback_data=f"progress_excellent_{registration_id}"),
            InlineKeyboardButton(text="✅ Хорошо", callback_data=f"progress_good_{registration_id}")
        ],
        [
            InlineKeyboardButton(text="📝 Удовл.", callback_data=f"progress_fair_{registration_id}"),
            InlineKeyboardButton(text="⚠️ Помощь", callback_data=f"progress_help_{registration_id}")
        ],
        [InlineKeyboardButton(text="✏️ Свой комментарий", callback_data=f"progress_custom_{registration_id}")],
        [_create_back_button(f"admin_back_{registration_id}")[0]]
    ])
    return keyboard


# Дополнительные функции для управления
def get_admin_management_keyboard():
    """Управление администраторами"""
    return get_admin_admins_menu()


def get_teacher_management_keyboard():
    """Управление преподавателями"""
    return get_admin_teachers_menu()


def get_course_management_keyboard():
    """Управление курсами"""
    return get_admin_courses_menu()


def get_student_management_keyboard():
    """Управление студентами"""
    return get_admin_students_menu()


def get_admin_keyboard():
    """Базовая клавиатура админа"""
    return get_admin_main_keyboard()
