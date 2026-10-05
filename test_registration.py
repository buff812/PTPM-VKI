"""Проверки правил, границ, маскирования и журналирования."""
import io
import logging
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from registration import load_mask_key, mask_password, register_user, validate_registration

GOOD = 'Абвгде1!'


class ValidationTests(unittest.TestCase):
    def test_valid_logins(self):
        for login in ('user_1', 'abcde', '12345', 'a.b+tag@example.com',
                      'user@example.co.uk', '+7-913-123-4567'):
            with self.subTest(login=login):
                self.assertEqual(validate_registration(login, GOOD, GOOD), (True, ''))

    def test_all_failure_reasons(self):
        cases = [
            (None, GOOD, GOOD, 'строками'),
            ('', GOOD, GOOD, 'пустым'),
            ('AdMiN', GOOD, GOOD, 'чёрном'),
            ('a@b', GOOD, GOOD, 'email'),
            ('+7(913)1234567', GOOD, GOOD, 'телефон'),
            ('abcd', GOOD, GOOD, 'минимум 5'),
            ('логин', GOOD, GOOD, 'латиницу'),
            ('student', '', '', 'пустым'),
            ('student', 'Аб1!', 'Аб1!', 'минимум 7'),
            ('student', 'Абвг 12!', 'Абвг 12!', 'пробельные'),
            ('student', 'Абвгдe1!', 'Абвгдe1!', 'латинские'),
            ('student', 'Абвгде1🙂', 'Абвгде1🙂', 'недопустимые'),
            ('student', 'абвгде1!', 'абвгде1!', 'заглавную'),
            ('student', 'АБВГДЕ1!', 'АБВГДЕ1!', 'строчную'),
            ('student', 'Абвгдеё!', 'Абвгдеё!', 'цифру'),
            ('student', 'Абвгде12', 'Абвгде12', 'спецсимвол'),
            ('student', GOOD, GOOD + '2', 'не совпадают'),
        ]
        messages = set()
        for login, password, confirmation, fragment in cases:
            with self.subTest(fragment=fragment):
                success, message = validate_registration(login, password, confirmation)
                self.assertFalse(success)
                self.assertIn(fragment, message)
                messages.add(message)
        self.assertEqual(len(messages), 17)

    def test_password_length_boundary_and_yo(self):
        self.assertEqual(validate_registration('abcde', 'Ёё1234!', 'Ёё1234!'), (True, ''))
        self.assertFalse(validate_registration('abcde', 'Ёё123!', 'Ёё123!')[0])

    def test_invalid_email_and_phone_boundaries(self):
        for login in ('a..b@example.com', '.a@example.com', 'a@-example.com',
                      'a@example-.com', 'a@b@c.com', 'a' * 65 + '@example.com',
                      'user@example.com\n', '+7-913-123-45678', '+7-913-123-4567\n',
                      '+٧-913-123-4567', '7-913-123-4567'):
            with self.subTest(login=login):
                self.assertFalse(validate_registration(login, GOOD, GOOD)[0])

    def test_no_implicit_trimming(self):
        self.assertFalse(validate_registration(' student', GOOD, GOOD)[0])
        self.assertFalse(validate_registration('student', GOOD + ' ', GOOD + ' ')[0])


class SecurityAndLoggingTests(unittest.TestCase):
    def setUp(self):
        self.key = b'k' * 32

    def test_mask_equal_different_and_not_plaintext(self):
        first = mask_password(GOOD, self.key)
        self.assertEqual(first, mask_password(GOOD, self.key))
        self.assertNotEqual(first, mask_password(GOOD + '2', self.key))
        self.assertNotEqual(first, mask_password(GOOD, b'z' * 32))
        self.assertNotIn(GOOD, first)

    def test_key_persists_and_corruption_is_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'secrets' / 'key'
            first = load_mask_key(path)
            self.assertEqual(len(first), 32)
            self.assertEqual(first, load_mask_key(path))
            path.write_bytes(b'bad')
            with self.assertRaises(ValueError):
                load_mask_key(path)

    def test_success_and_failure_logged_without_passwords(self):
        with self.assertLogs('registration', level='INFO') as logs:
            self.assertEqual(register_user('student', GOOD, GOOD, self.key), (True, ''))
            self.assertFalse(register_user('student', GOOD, GOOD + '2', self.key)[0])
        text = '\n'.join(logs.output)
        self.assertNotIn(GOOD, text)
        self.assertIn('masked:', text)
        self.assertIn('True', text)
        self.assertIn('False', text)

    def test_exception_traceback_is_redacted(self):
        with patch('registration.validate_registration', side_effect=RuntimeError('Сбой: ' + GOOD)):
            with self.assertLogs('registration', level='ERROR') as logs:
                result = register_user('student', GOOD, GOOD, self.key)
        text = '\n'.join(logs.output)
        self.assertFalse(result[0])
        self.assertIn('Traceback', text)
        self.assertIn('RuntimeError', text)
        self.assertNotIn(GOOD, text)

    def test_password_equal_to_login_is_redacted(self):
        with self.assertLogs('registration', level='INFO') as logs:
            register_user('student', 'student', 'student', self.key)
        self.assertNotIn('student', '\n'.join(logs.output))

    def test_two_handlers_receive_same_safe_events(self):
        logger = logging.getLogger('registration')
        old_handlers, old_level, old_propagate = logger.handlers[:], logger.level, logger.propagate
        console = io.StringIO()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'registration.log'
            stream_handler = logging.StreamHandler(console)
            file_handler = logging.FileHandler(path, encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
            for handler in (stream_handler, file_handler):
                handler.setFormatter(formatter)
            logger.handlers = [stream_handler, file_handler]
            logger.setLevel(logging.DEBUG)
            logger.propagate = False
            try:
                register_user('student', GOOD, GOOD, self.key)
                register_user('admin', GOOD, GOOD, self.key)
                file_handler.flush()
                file_text = path.read_text(encoding='utf-8')
                self.assertEqual(console.getvalue(), file_text)
                self.assertNotIn(GOOD, file_text)
                self.assertIn('Запрос', file_text)
                self.assertIn('True', file_text)
                self.assertIn('False', file_text)
            finally:
                logger.handlers, logger.level, logger.propagate = old_handlers, old_level, old_propagate
                file_handler.close()
                stream_handler.close()


if __name__ == '__main__':
    unittest.main()
