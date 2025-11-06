import re
import logging
from typing import Optional
from config import Config
from database import Database

config = Config()
logger = logging.getLogger(__name__)
db = Database(config.DB_NAME)


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    from database import Database
    from config import Config

    db = Database(Config().DB_NAME)
    admins = db.get_all_admins()

    admin_ids = [admin['user_id'] for admin in admins if admin.get('is_active')]
    return user_id in admin_ids


def extract_id(text: str) -> Optional[int]:
    """Извлечение ID из текста"""
    try:
        match = re.search(r'\((\d+)\)', text)
        if match:
            return int(match.group(1))
        if text and text.strip().isdigit():
            return int(text.strip())
        return None
    except Exception as e:
        logger.error(f"Error extracting ID from '{text}': {e}")
        return None


def get_grade_from_progress(progress: float) -> str:
    """Получить оценку на основе прогресса"""
    for grade, threshold in config.GRADING_SCALE.items():
        if progress >= threshold:
            return grade
    return 'F'


def get_student_by_id(student_id: int):
    """Получить студента по ID"""
    return db.get_student_by_id(student_id)
