import unittest

from src.database import (
    MAX_MESSAGE_LENGTH,
    MAX_NAME_LENGTH,
    DatabaseRepository,
    DuplicateIdError,
    RecordNotFoundError,
    ValidationError,
)


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.repo = DatabaseRepository(":memory:")

    def tearDown(self):
        self.repo.close()


class TestAdd(DatabaseTestCase):
    def test_add_success(self):
        self.assertTrue(self.repo.add(1, "alice", "<p>Привет</p>"))
        self.assertEqual(
            self.repo.get_by_id(1),
            {"id": 1, "name": "alice", "message": "<p>Привет</p>"},
        )

    def test_add_duplicate_id_raises(self):
        self.repo.add(1, "alice", "first")
        with self.assertRaises(DuplicateIdError):
            self.repo.add(1, "bob", "second")

    def test_add_name_too_long_raises(self):
        with self.assertRaises(ValidationError):
            self.repo.add(1, "a" * (MAX_NAME_LENGTH + 1), "text")

    def test_add_message_too_long_raises(self):
        with self.assertRaises(ValidationError):
            self.repo.add(1, "alice", "m" * (MAX_MESSAGE_LENGTH + 1))

    def test_add_wrong_types_raise(self):
        with self.assertRaises(ValidationError):
            self.repo.add("1", "alice", "text")
        with self.assertRaises(ValidationError):
            self.repo.add(1, 123, "text")
        with self.assertRaises(ValidationError):
            self.repo.add(1, "alice", None)

    def test_add_max_length_boundaries_allowed(self):
        self.assertTrue(
            self.repo.add(1, "a" * MAX_NAME_LENGTH, "m" * MAX_MESSAGE_LENGTH)
        )


class TestGetById(DatabaseTestCase):
    def test_get_by_id_found(self):
        self.repo.add(5, "alice", "hello")
        record = self.repo.get_by_id(5)
        self.assertEqual(record["name"], "alice")
        self.assertEqual(record["message"], "hello")

    def test_get_by_id_missing_returns_none(self):
        self.assertIsNone(self.repo.get_by_id(404))

    def test_get_by_id_wrong_type_raises(self):
        with self.assertRaises(ValidationError):
            self.repo.get_by_id("5")


class TestGetByName(DatabaseTestCase):
    def test_get_by_name_returns_all_user_records(self):
        self.repo.add(1, "alice", "one")
        self.repo.add(2, "bob", "two")
        self.repo.add(3, "alice", "three")
        records = self.repo.get_by_name("alice")
        self.assertEqual([r["id"] for r in records], [1, 3])

    def test_get_by_name_unknown_returns_empty_list(self):
        self.repo.add(1, "alice", "one")
        self.assertEqual(self.repo.get_by_name("nobody"), [])

    def test_get_by_name_wrong_type_raises(self):
        with self.assertRaises(ValidationError):
            self.repo.get_by_name(None)


class TestUpdate(DatabaseTestCase):
    def test_update_existing_record(self):
        self.repo.add(1, "alice", "old")
        self.assertTrue(self.repo.update(1, "new"))
        self.assertEqual(self.repo.get_by_id(1)["message"], "new")

    def test_update_missing_id_raises(self):
        with self.assertRaises(RecordNotFoundError):
            self.repo.update(999, "text")

    def test_update_too_long_message_raises(self):
        self.repo.add(1, "alice", "old")
        with self.assertRaises(ValidationError):
            self.repo.update(1, "m" * (MAX_MESSAGE_LENGTH + 1))
        self.assertEqual(self.repo.get_by_id(1)["message"], "old")


class TestDelete(DatabaseTestCase):
    def test_delete_existing_record(self):
        self.repo.add(1, "alice", "text")
        self.assertTrue(self.repo.delete(1))
        self.assertIsNone(self.repo.get_by_id(1))

    def test_delete_missing_returns_false(self):
        self.assertFalse(self.repo.delete(999))

    def test_delete_keeps_other_records(self):
        self.repo.add(1, "alice", "one")
        self.repo.add(2, "bob", "two")
        self.repo.delete(1)
        self.assertIsNotNone(self.repo.get_by_id(2))


if __name__ == "__main__":
    unittest.main()
