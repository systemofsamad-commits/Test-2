import re


def validate_name(name: str) -> tuple[bool, str]:
    if not name or len(name) < 2:
        return False, "Имя слишком короткое"
    if len(name) > 100:
        return False, "Имя слишком длинное"
    return True, ""


def validate_phone(phone: str) -> tuple[bool, str]:
    clean_phone = re.sub(r'[^\d+]', '', phone)
    if len(clean_phone) < 9:
        return False, "Номер слишком короткий"
    return True, ""


def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def format_phone(phone: str) -> str:
    clean_phone = re.sub(r'[^\d+]', '', phone)
    if not clean_phone.startswith('+'):
        clean_phone = '+' + clean_phone
    return clean_phone
