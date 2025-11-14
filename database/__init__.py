"""
database Module
Модуль для работы с базой данных образовательного центра
"""

from .base import Database

# Singleton instance
_db_instance = None


def get_db() -> Database:
    """
    Получить единственный экземпляр БД (Singleton pattern)

    Returns:
        Database: Экземпляр базы данных

    Example:
        >>> from database import get_db
        >>> db = get_db()
        >>> students = db.students.get_all_active()
    """
    global _db_instance
    if _db_instance is None:
        from config import Config
        _db_instance = Database(Config.DB_NAME)
    return _db_instance


def reset_db():
    """Сбросить singleton (для тестирования)"""
    global _db_instance
    _db_instance = None


__all__ = ['Database', 'get_db', 'reset_db']


def users():
    return None
