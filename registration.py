"""Вариант 2: проверка данных и безопасное журналирование запросов."""
import hmac
import logging
import re
import string
import traceback
from pathlib import Path
import secrets

LOGGER = logging.getLogger(__name__)
BLACKLIST = frozenset({'admin', 'administrator', 'root', 'superuser', 'support', 'testuser'})
SPECIALS = frozenset(string.punctuation)
PHONE = re.compile(r'\+[0-9]-[0-9]{3}-[0-9]{3}-[0-9]{4}')
USERNAME = re.compile(r'[A-Za-z0-9_]+')
# Учебная практическая маска, а не полная реализация стандарта email.
EMAIL = re.compile(
    r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*@"
    r'(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+'
    r'[A-Za-z]{2,63}'
)


def validate_registration(login: str, password: str, confirmation: str) -> tuple[bool, str]:
    """Возвращает (успех, первая причина отказа). Не изменяет входные строки."""
    if not all(isinstance(value, str) for value in (login, password, confirmation)):
        return False, 'Все три входных значения должны быть строками.'
    if not login:
        return False, 'Логин не должен быть пустым.'
    if login.casefold() in BLACKLIST:
        return False, 'Логин находится в чёрном списке.'
    if '@' in login:
        if len(login) > 254 or len(login.split('@', 1)[0]) > 64 or not EMAIL.fullmatch(login):
            return False, 'Некорректный email: ожидается адрес вида name@example.com.'
    elif login.startswith('+') or ('-' in login and login[:1].isdigit()):
        if not PHONE.fullmatch(login):
            return False, 'Некорректный телефон: ожидается формат +x-xxx-xxx-xxxx.'
    else:
        if len(login) < 5:
            return False, 'Обычный логин должен содержать минимум 5 символов.'
        if not USERNAME.fullmatch(login):
            return False, 'Обычный логин допускает только латиницу, цифры и знак _.'
    if not password:
        return False, 'Пароль не должен быть пустым.'
    if len(password) < 7:
        return False, 'Пароль должен содержать минимум 7 символов.'
    if any(char.isspace() for char in password):
        return False, 'Пароль не должен содержать пробельные символы.'
    if any('A' <= char <= 'Z' or 'a' <= char <= 'z' for char in password):
        return False, 'Пароль не должен содержать латинские буквы.'
    if any(not ('А' <= char <= 'я' or char in 'Ёё' or '0' <= char <= '9' or char in SPECIALS)
           for char in password):
        return False, 'Пароль содержит недопустимые символы.'
    if not any('А' <= char <= 'Я' or char == 'Ё' for char in password):
        return False, 'Пароль должен содержать хотя бы одну заглавную русскую букву.'
    if not any('а' <= char <= 'я' or char == 'ё' for char in password):
        return False, 'Пароль должен содержать хотя бы одну строчную русскую букву.'
    if not any('0' <= char <= '9' for char in password):
        return False, 'Пароль должен содержать хотя бы одну цифру.'
    if not any(char in SPECIALS for char in password):
        return False, 'Пароль должен содержать хотя бы один спецсимвол.'
    if password != confirmation:
        return False, 'Пароль и подтверждение пароля не совпадают.'
    return True, ''


def load_mask_key(path: Path) -> bytes:
    """Ключ сохраняется между запусками, но не отправляется в Git."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('xb') as stream:
            stream.write(secrets.token_bytes(32))
        path.chmod(0o600)
    except FileExistsError:
        pass
    key = path.read_bytes()
    if len(key) != 32:
        raise ValueError('Файл ключа повреждён: необходимо 32 байта.')
    return key


def mask_password(password: str, key: bytes) -> str:
    """Полный HMAC-SHA256; исходный пароль не попадает в журнал."""
    digest = hmac.new(key, password.encode('utf-8', errors='surrogatepass'), 'sha256').hexdigest()
    return f'<masked:{digest}>'


def redact(text: str, password: str, confirmation: str) -> str:
    """Удаляет секреты также из текста исключения и совпадающего логина."""
    variants = set()
    for value in (password, confirmation):
        if isinstance(value, str) and value:
            variants.add(value)
            variants.add(repr(value)[1:-1])
    for value in sorted(variants, key=len, reverse=True):
        text = text.replace(value, '<redacted>')
    return text


def register_user(login: str, password: str, confirmation: str, key: bytes) -> tuple[bool, str]:
    """Граница запроса: маскирование, проверка, результат и перехват сбоя."""
    if not all(isinstance(value, str) for value in (login, password, confirmation)):
        result = (False, 'Все три входных значения должны быть строками.')
        LOGGER.warning('Запрос отклонён: %s', result[1])
        return result
    params = (f'login={redact(repr(login), password, confirmation)}, '
              f'password={mask_password(password, key)}, '
              f'confirmation={mask_password(confirmation, key)}')
    LOGGER.info('Запрос: %s', params)
    try:
        success, message = validate_registration(login, password, confirmation)
        if success:
            LOGGER.info('Результат: True; сообщение=%r; %s', message, params)
        else:
            LOGGER.warning('Результат: False; причина=%s; %s', message, params)
        return success, message
    except Exception:
        # Сначала очищаем traceback, затем передаём его логгеру.
        # capture locals не используется: содержимое переменных не печатается.
        safe_traceback = redact(traceback.format_exc(), password, confirmation)
        LOGGER.error('Сбой запроса; %s\n%s', params, safe_traceback)
        return False, 'Внутренняя ошибка проверки. Подробности записаны в журнал.'
