import sys

from src import DatabaseRepository, ForumParser

DEFAULT_URL = "https://habr.com/ru/articles/1105048/comments/"


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    repository = DatabaseRepository("comments.db")
    parser = ForumParser()
    comments = parser.parse_page(url)
    saved = parser.save_to_db(comments, repository)
    print(f"Найдено комментариев: {len(comments)}, сохранено новых: {saved}")


if __name__ == "__main__":
    main()
