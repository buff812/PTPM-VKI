import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.database import DatabaseRepository
from src.parser import ForumParser

FIXTURE = Path(__file__).parent / "fixtures" / "habr_comments.html"


class TestForumParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = FIXTURE.read_text(encoding="utf-8")

    def setUp(self):
        self.parser = ForumParser()
        self.comments = self.parser.parse_html(self.html)

    def test_parse_extracts_id_name_and_message(self):
        first = self.comments[0]
        self.assertIsInstance(first["id"], int)
        self.assertTrue(first["name"])
        self.assertTrue(first["message"])
        self.assertEqual(first["id"], 30615476)
        self.assertEqual(first["name"], "WhiteSorcerer")
        self.assertEqual(first["message"], "<p>Походу Бегет не успел обновиться.</p>")

    def test_parse_skips_comment_without_author(self):
        ids = [c["id"] for c in self.comments]
        self.assertNotIn(999001, ids)
        self.assertEqual(len(self.comments), 4)

    def test_parse_empty_page_returns_empty_list(self):
        self.assertEqual(self.parser.parse_html("<html><body></body></html>"), [])

    def test_save_to_db_stores_all_comments(self):
        repo = DatabaseRepository(":memory:")
        saved = self.parser.save_to_db(self.comments, repo)
        self.assertEqual(saved, 4)
        self.assertEqual(repo.get_by_id(30615476)["name"], "WhiteSorcerer")
        repo.close()

    def test_save_to_db_ignores_duplicates(self):
        repo = DatabaseRepository(":memory:")
        self.parser.save_to_db(self.comments, repo)
        self.assertEqual(self.parser.save_to_db(self.comments, repo), 0)
        repo.close()

    def test_parse_page_sends_user_agent_header(self):
        response = MagicMock(text=self.html)
        with patch("src.parser.requests.get", return_value=response) as mocked_get:
            comments = self.parser.parse_page("https://example.com/comments/")
        _, kwargs = mocked_get.call_args
        self.assertIn("User-Agent", kwargs["headers"])
        self.assertEqual(len(comments), 4)


if __name__ == "__main__":
    unittest.main()
