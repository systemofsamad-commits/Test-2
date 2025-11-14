"""
Вспомогательные функции
Модуль содержит утилиты для работы с данными, валидации и форматирования
"""
import re
import logging
from typing import Optional

from config import Config

config = Config()
logger = logging.getLogger(__name__)

# Singleton для базы данных
_db_instance = None


def get_db():
    """Получить единственный экземпляр Database (Singleton)
    :rtype: Database
    """
    global _db_instance

    if _db_instance is None:
        from database import Database
        _db_instance = Database(config.DB_NAME)
        logger.info("✅ Database singleton created")

    return _db_instance


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    try:
        # Проверяем в БД
        db = get_db()
        query = "SELECT 1 FROM admins WHERE user_id = ? AND is_active = 1 LIMIT 1"
        result = db.execute_query(query, (user_id,))

        if result:
            return True

        # Fallback на статический список
        return user_id in config.ADMIN_IDS

    except Exception as e:
        logger.error(f"Error checking admin: {e}")
        return user_id in config.ADMIN_IDS


def extract_id(text: str) -> Optional[int]:
    """Извлечение ID из текста"""
    try:
        match = re.search(r'\((\d+)\)', text)
        if match:
            return int(match.group(1))

        match = re.search(r'#(\d+)', text)
        if match:
            return int(match.group(1))

        if text and text.strip().isdigit():
            return int(text.strip())

        return None
    except Exception as e:
        logger.error(f"Error extracting ID: {e}")
        return None


def get_grade_from_progress(progress: float) -> str:
    """
    Получить оценку на основе прогресса

    Args:
        progress: Процент прогресса (0-100)

    Returns:
        str: Буквенная оценка (A-F)
    """
    # Проверяем есть ли шкала оценок в config
    if hasattr(config, 'GRADING_SCALE'):
        for grade, threshold in config.GRADING_SCALE.items():
            if progress >= threshold:
                return grade

    # Стандартная шкала оценок
    if progress >= 90:
        return 'A'
    elif progress >= 80:
        return 'B'
    elif progress >= 70:
        return 'C'
    elif progress >= 60:
        return 'D'
    else:
        return 'F'


def get_student_by_id(student_id: int):
    """
    Получить студента по ID регистрации

    Args:
        student_id: ID регистрации студента

    Returns:
        Dict: Данные студента или None
    """
    try:
        db = get_db()
        return db.registrations.get_by_id(student_id)
    except Exception as e:
        logger.error(f"Error getting student {student_id}: {e}")
        return None


def format_phone(phone: str) -> str:
    """
    Форматировать номер телефона

    Args:
        phone: Телефон в любом формате

    Returns:
        str: Форматированный телефон
    """
    if not phone:
        return ""

    # Убираем все кроме цифр
    digits = re.sub(r'\D', '', phone)

    # Форматируем для Узбекистана
    if digits.startswith('998') and len(digits) == 12:
        return f"+{digits[0:3]} ({digits[3:5]}) {digits[5:8]}-{digits[8:10]}-{digits[10:12]}"

    # Если начинается без кода страны
    if len(digits) == 9:
        digits = '998' + digits
        return f"+{digits[0:3]} ({digits[3:5]}) {digits[5:8]}-{digits[8:10]}-{digits[10:12]}"

    # Возвращаем как есть если не подходит
    return phone if phone.startswith('+') else f"+{phone}"


def format_price(price: int) -> str:
    """Форматировать цену"""
    return f"{price:,}".replace(',', ' ') + ' сум'


def get_status_emoji(status: str) -> str:
    """Получить emoji для статуса"""
    status_emojis = {
        'active': '✅',
        'trial': '🎯',
        'studying': '📚',
        'frozen': '❄️',
        'waiting_payment': '💰',
        'completed': '🎓'
    }
    return status_emojis.get(status, '📋')


def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезать текст"""
    if not text or len(text) <= max_length:
        return text or ""
    return text[:max_length - 3] + "..."


def escape_markdown(text: str) -> str:
    """Экранировать спецсимволы для Markdown"""
    if not text:
        return ""

    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def validate_phone(phone: str) -> bool:
    """Проверить телефон"""
    if not phone:
        return False
    digits = re.sub(r'\D', '', phone)
    return len(digits) >= 9


def validate_email(email: str) -> bool:
    """Проверить email"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_name(name: str) -> bool:
    """
    Проверить корректность имени

    Args:
        name: Имя для проверки

    Returns:
        bool: True если имя корректное
    """
    if not name or len(name.strip()) < 2:
        return False

    # Проверяем что есть буквы (не только цифры/символы)
    if not re.search(r'[a-zA-Zа-яА-ЯёЁ]', name):
        return False

    return True


def validate_rating(rating: int) -> bool:
    """Проверить рейтинг (1-5)"""
    return isinstance(rating, int) and 1 <= rating <= 5


def get_user_link(user_id: int, username: Optional[str] = None, full_name: Optional[str] = None) -> str:
    """
    Создать HTML ссылку на пользователя

    Args:
        user_id: Telegram ID
        username: Username (опционально)
        full_name: Полное имя (опционально)

    Returns:
        str: HTML ссылка
    """
    if username:
        return f'<a href="https://t.me/{username}">@{username}</a>'
    elif full_name:
        return f'<a href="tg://user?id={user_id}">{full_name}</a>'
    else:
        return f'<a href="tg://user?id={user_id}">User {user_id}</a>'