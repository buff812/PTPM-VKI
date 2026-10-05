"""Точка входа: python main.py или python main.py --demo."""
import argparse
from getpass import getpass
import logging
from pathlib import Path
import sys

from registration import load_mask_key, register_user

BASE_DIR = Path(__file__).resolve().parent


def configure_logging() -> None:
    logs = BASE_DIR / 'Logs'
    logs.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s | [%(levelname)-7s] | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(sys.stdout),
                  logging.FileHandler(logs / 'registration.log', encoding='utf-8')],
        force=True,
    )


def Main() -> None:
    configure_logging()
    logging.info('Логгер настроен. Приложение запущено.')
    parser = argparse.ArgumentParser(description='Лабораторная №1, вариант 2')
    parser.add_argument('--demo', action='store_true', help='Запустить готовые примеры')
    parser.add_argument('--visible-input', action='store_true',
                        help='Обычный ввод паролей для окна Run в PyCharm (символы видны)')
    args = parser.parse_args()
    try:
        key = load_mask_key(BASE_DIR / '.secrets' / 'mask.key')
    except OSError:
        logging.exception('Не удалось открыть или создать ключ маскирования.')
        return
    except ValueError:
        logging.exception('Не удалось загрузить ключ маскирования.')
        return
    if args.demo:
        cases = [('student_1', 'Абвгде1!', 'Абвгде1!'),
                 ('student@example.com', 'Ёжик123!', 'Ёжик123!'),
                 ('+7-913-123-4567', 'Абвгде1!', 'Абвгде1!'),
                 ('admin', 'Абвгде1!', 'Абвгде1!'),
                 ('student_1', 'abcdef1!', 'abcdef1!'),
                 ('student_1', 'Абвгде1!', 'Абвгде2!')]
        for login, password, confirmation in cases:
            success, message = register_user(login, password, confirmation, key)
            print(f'Результат: {success}; сообщение: {message!r}')
    else:
        print('Проверка регистрации. Данные пользователя не сохраняются.')
        if args.visible_input:
            print('Пароли видны при вводе. Используйте учебные данные.')
        read_password = input if args.visible_input else getpass
        while True:
            try:
                login = input('\nЛогин: ')
                password = read_password('Пароль: ')
                confirmation = read_password('Подтверждение пароля: ')
                success, message = register_user(login, password, confirmation, key)
                print(f'Результат: {success}')
                print('Данные прошли проверку.' if success else message)
                if input('Проверить ещё раз? [да/нет]: ').strip().lower() not in ('да', 'д', 'y', 'yes'):
                    break
            except (EOFError, KeyboardInterrupt):
                print('\nВвод завершён.')
                break
    logging.info('Приложение завершено.')


if __name__ == '__main__':
    Main()
