import requests
from bs4 import BeautifulSoup

from .database import DuplicateIdError, ValidationError

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

COMMENT_SELECTOR = "article.tm-comment-thread__comment"
AUTHOR_SELECTOR = "a.tm-user-info__username"
BODY_SELECTOR = "div.tm-comment__body-content"


class ForumParser:
    def __init__(self, headers=None, timeout=15):
        self.headers = headers or DEFAULT_HEADERS
        self.timeout = timeout

    def fetch(self, url):
        response = requests.get(url, headers=self.headers, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def parse_html(self, html):
        soup = BeautifulSoup(html, "lxml")
        comments = []
        for article in soup.select(COMMENT_SELECTOR):
            comment = self._parse_comment(article)
            if comment is not None:
                comments.append(comment)
        return comments

    def parse_page(self, url):
        return self.parse_html(self.fetch(url))

    @staticmethod
    def _parse_comment(article):
        raw_id = article.get("id", "")
        author = article.select_one(AUTHOR_SELECTOR)
        body = article.select_one(BODY_SELECTOR)
        if not raw_id.isdigit() or author is None or body is None:
            return None
        name = author.get_text(strip=True)
        message = body.decode_contents().strip()
        if not name or not message:
            return None
        return {"id": int(raw_id), "name": name, "message": message}

    @staticmethod
    def save_to_db(parsed_data, repository):
        saved = 0
        for item in parsed_data:
            try:
                repository.add(item["id"], item["name"], item["message"])
                saved += 1
            except (DuplicateIdError, ValidationError):
                continue
        return saved
