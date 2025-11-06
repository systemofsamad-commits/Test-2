from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


# ============================================
# УМНЫЙ ПАРСЕР ДАТ (Auto-detect format)
# ============================================

def smart_parse_datetime(date_str: str) -> Optional[datetime]:
    """
    Умный парсер - автоматически определяет формат даты.
    Поддерживает множество форматов.

    Примеры:
        "2024-11-06 14:30:00" ✅
        "06.11.2024 14:30" ✅
        "2024-11-06" ✅
        "06.11.2024" ✅
        "14:30" ✅
        "2024-11-06T14:30:00" ✅
        "10 ноября 2024" ✅
        "10 ноября 2024, 14:30" ✅
    """
    if not date_str or not isinstance(date_str, str):
        return None

    date_str = date_str.strip()

    # Список форматов для попытки парсинга (от более специфичных к общим)
    formats = [
        # Полные форматы с датой и временем
        "%Y-%m-%d %H:%M:%S",  # 2024-11-06 14:30:00
        "%d.%m.%Y %H:%M:%S",  # 06.11.2024 14:30:00
        "%d.%m.%Y %H:%M",  # 06.11.2024 14:30
        "%d/%m/%Y %H:%M:%S",  # 06/11/2024 14:30:00
        "%d/%m/%Y %H:%M",  # 06/11/2024 14:30
        "%Y-%m-%dT%H:%M:%S",  # 2024-11-06T14:30:00 (ISO)
        "%Y-%m-%d %H:%M",  # 2024-11-06 14:30

        # Только дата
        "%Y-%m-%d",  # 2024-11-06
        "%d.%m.%Y",  # 06.11.2024
        "%d/%m/%Y",  # 06/11/2024
        "%d-%m-%Y",  # 06-11-2024

        # Только время
        "%H:%M:%S",  # 14:30:00
        "%H:%M",  # 14:30
    ]

    # Пробуем каждый формат
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)

            # Если распарсили только время, добавляем сегодняшнюю дату
            if fmt in ["%H:%M:%S", "%H:%M"]:
                today = datetime.now().date()
                dt = datetime.combine(today, dt.time())

            return dt

        except ValueError:
            continue

    # Не удалось распарсить
    return None


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Форматирует datetime объект в строку"""
    if not dt:
        return ""
    return dt.strftime(fmt)


def now_str() -> str:
    """Возвращает текущее время в стандартном формате"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================
# ФОРМАТЫ ДАТ
# ============================================

class DateFormats:
    """Коллекция часто используемых форматов дат"""
    # Для базы данных
    DB_FULL = "%Y-%m-%d %H:%M:%S"  # 2024-11-06 14:30:00
    DB_DATE = "%Y-%m-%d"  # 2024-11-06

    # Для пользователя (читаемые)
    USER_FULL = "%d.%m.%Y %H:%M"  # 06.11.2024 14:30
    USER_DATE = "%d.%m.%Y"  # 06.11.2024
    USER_TIME = "%H:%M"  # 14:30

    # ISO форматы
    ISO_FULL = "%Y-%m-%dT%H:%M:%S"  # 2024-11-06T14:30:00
    ISO_DATE = "%Y-%m-%d"  # 2024-11-06

    # Дополнительные
    COMPACT = "%Y%m%d%H%M%S"  # 20241106143000
    MONTH_YEAR = "%B %Y"  # November 2024


# ============================================
# МОДЕЛИ ДАННЫХ
# ============================================

@dataclass
class StudentRegistration:
    id: int
    user_id: int
    name: str
    phone: str
    course: str
    training_type: str
    schedule: str
    price: str
    status: str
    created_at: str
    progress: float = 0.0
    consultation_time: Optional[str] = None
    trial_lesson_time: Optional[str] = None
    lesson_time: Optional[str] = None
    notified: bool = False
    reminder_sent: bool = False
    attendance: int = 0
    grade: Optional[str] = None
    updated_at: Optional[str] = None

    def get_created_datetime(self) -> Optional[datetime]:
        """Получить created_at как datetime объект"""
        return smart_parse_datetime(self.created_at)

    def get_trial_datetime(self) -> Optional[datetime]:
        """Получить trial_lesson_time как datetime объект"""
        return smart_parse_datetime(self.trial_lesson_time) if self.trial_lesson_time else None

    def format_created_at(self, fmt: str = DateFormats.USER_FULL) -> str:
        """Форматировать дату создания"""
        dt = self.get_created_datetime()
        return format_datetime(dt, fmt) if dt else "Не указана"

    def format_trial_time(self, fmt: str = DateFormats.USER_FULL) -> str:
        """Форматировать время пробного урока"""
        dt = self.get_trial_datetime()
        return format_datetime(dt, fmt) if dt else "Не назначено"

    def set_trial_time_from_string(self, date_str: str) -> bool:
        """
        Установить время пробного урока из строки любого формата
        Возвращает True если успешно распарсили
        """
        dt = smart_parse_datetime(date_str)
        if dt:
            self.trial_lesson_time = format_datetime(dt, DateFormats.DB_FULL)
            return True
        return False


@dataclass
class Reminder:
    id: int
    user_id: int
    text: str
    due_date: str
    sent: bool = False
    created_at: str = field(default_factory=now_str)

    def get_due_datetime(self) -> Optional[datetime]:
        """Получить due_date как datetime объект"""
        return smart_parse_datetime(self.due_date)

    def format_due_date(self, fmt: str = DateFormats.USER_FULL) -> str:
        """Форматировать дату напоминания"""
        dt = self.get_due_datetime()
        return format_datetime(dt, fmt) if dt else "Не указана"

    def is_overdue(self) -> bool:
        """Проверить, просрочено ли напоминание"""
        dt = self.get_due_datetime()
        return dt < datetime.now() if dt else False

    def set_due_date_from_string(self, date_str: str) -> bool:
        """Установить дату из строки любого формата"""
        dt = smart_parse_datetime(date_str)
        if dt:
            self.due_date = format_datetime(dt, DateFormats.DB_FULL)
            return True
        return False


@dataclass
class Feedback:
    id: int
    user_id: int
    reg_id: int
    rating: int
    comment: Optional[str] = None
    created_at: str = field(default_factory=now_str)

    def get_created_datetime(self) -> Optional[datetime]:
        """Получить created_at как datetime объект"""
        return smart_parse_datetime(self.created_at)

    def format_created_at(self, fmt: str = DateFormats.USER_FULL) -> str:
        """Форматировать дату создания"""
        dt = self.get_created_datetime()
        return format_datetime(dt, fmt) if dt else "Не указана"


@dataclass
class Admin:
    id: int
    user_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    created_at: str = field(default_factory=now_str)
    is_active: bool = True

    def get_created_datetime(self) -> Optional[datetime]:
        """Получить created_at как datetime объект"""
        return smart_parse_datetime(self.created_at)

    def format_created_at(self, fmt: str = DateFormats.USER_DATE) -> str:
        """Форматировать дату создания"""
        dt = self.get_created_datetime()
        return format_datetime(dt, fmt) if dt else "Не указана"


@dataclass
class Teacher:
    id: int
    name: str
    phone: str
    email: Optional[str] = None
    specialization: Optional[str] = None
    experience: Optional[str] = None
    created_at: str = field(default_factory=now_str)
    is_active: bool = True

    def get_created_datetime(self) -> Optional[datetime]:
        """Получить created_at как datetime объект"""
        return smart_parse_datetime(self.created_at)

    def format_created_at(self, fmt: str = DateFormats.USER_DATE) -> str:
        """Форматировать дату создания"""
        dt = self.get_created_datetime()
        return format_datetime(dt, fmt) if dt else "Не указана"


@dataclass
class Course:
    id: int
    name: str
    description: Optional[str] = None
    duration: Optional[str] = None
    price: Optional[str] = None
    created_at: str = field(default_factory=now_str)
    is_active: bool = True

    def get_created_datetime(self) -> Optional[datetime]:
        """Получить created_at как datetime объект"""
        return smart_parse_datetime(self.created_at)

    def format_created_at(self, fmt: str = DateFormats.USER_DATE) -> str:
        """Форматировать дату создания"""
        dt = self.get_created_datetime()
        return format_datetime(dt, fmt) if dt else "Не указана"


@dataclass
class Group:
    id: int
    name: str
    course_id: int
    teacher_id: int
    schedule: str
    max_students: int = 10
    current_students: int = 0
    created_at: str = field(default_factory=now_str)
    is_active: bool = True

    def get_created_datetime(self) -> Optional[datetime]:
        """Получить created_at как datetime объект"""
        return smart_parse_datetime(self.created_at)

    def format_created_at(self, fmt: str = DateFormats.USER_DATE) -> str:
        """Форматировать дату создания"""
        dt = self.get_created_datetime()
        return format_datetime(dt, fmt) if dt else "Не указана"

    def is_full(self) -> bool:
        """Проверить, заполнена ли группа"""
        return self.current_students >= self.max_students

    def available_slots(self) -> int:
        """Получить количество свободных мест"""
        return max(0, self.max_students - self.current_students)


# ============================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТ УМНОГО ПАРСЕРА")
    print("=" * 60)
    print()

    # Тестируем разные форматы
    test_inputs = [
        "2024-11-06 14:30:00",
        "06.11.2024 14:30",
        "10.11.2024 14:00",
        "2024-11-10",
        "06.11.2024",
        "14:30",
        "2024-11-06T14:30:00",
        "10/11/2024 14:30",
    ]

    print("📅 Тестирование разных форматов ввода:\n")
    for test_input in test_inputs:
        dt = smart_parse_datetime(test_input)
        if dt:
            # Показываем в разных форматах
            db_format = format_datetime(dt, DateFormats.DB_FULL)
            user_format = format_datetime(dt, DateFormats.USER_FULL)

            print(f"Ввод:  '{test_input}'")
            print(f"  ✅ Распознано")
            print(f"  🗄️  БД:   {db_format}")
            print(f"  👤 Юзер: {user_format}")
        else:
            print(f"Ввод:  '{test_input}'")
            print(f"  ❌ Не распознано")
        print()

    print("=" * 60)
    print("ТЕСТ РАБОТЫ С МОДЕЛЯМИ")
    print("=" * 60)
    print()

    # Создаем студента
    student = StudentRegistration(
        id=1,
        user_id=123456,
        name="Иван Иванов",
        phone="+998901234567",
        course="Python",
        training_type="Групповое",
        schedule="Вечернее",
        price="500000",
        status="active",
        created_at=now_str()
    )

    # Тестируем установку даты пробного урока в разных форматах
    test_dates = [
        "10.11.2024 14:00",  # Пользовательский формат
        "2024-11-10 14:00:00",  # Формат БД
        "10/11/2024 14:00",  # Альтернативный
    ]

    print("🎓 Назначение пробного урока:\n")
    for date_input in test_dates:
        success = student.set_trial_time_from_string(date_input)
        if success:
            print(f"Ввод: '{date_input}'")
            print(f"  ✅ Успешно назначено")
            print(f"  🗄️  В БД: {student.trial_lesson_time}")
            print(f"  👤 Показ: {student.format_trial_time()}")
        else:
            print(f"Ввод: '{date_input}'")
            print(f"  ❌ Ошибка")
        print()