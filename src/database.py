import sqlite3

MAX_NAME_LENGTH = 256
MAX_MESSAGE_LENGTH = 8096


class ValidationError(ValueError):
    pass


class DuplicateIdError(Exception):
    pass


class RecordNotFoundError(Exception):
    pass


class DatabaseRepository:
    def __init__(self, db_path=":memory:"):
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    message TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _validate_id(comment_id):
        if isinstance(comment_id, bool) or not isinstance(comment_id, int):
            raise ValidationError("id должен быть целым числом")

    @staticmethod
    def _validate_name(username):
        if not isinstance(username, str):
            raise ValidationError("name должен быть строкой")
        if not username.strip():
            raise ValidationError("name не может быть пустым")
        if len(username) > MAX_NAME_LENGTH:
            raise ValidationError(f"name длиннее {MAX_NAME_LENGTH} символов")

    @staticmethod
    def _validate_message(message):
        if not isinstance(message, str):
            raise ValidationError("message должен быть строкой")
        if not message.strip():
            raise ValidationError("message не может быть пустым")
        if len(message) > MAX_MESSAGE_LENGTH:
            raise ValidationError(f"message длиннее {MAX_MESSAGE_LENGTH} символов")

    @staticmethod
    def _row_to_dict(row):
        return dict(row) if row is not None else None

    def get_by_id(self, comment_id):
        self._validate_id(comment_id)
        row = self._connection.execute(
            "SELECT id, name, message FROM comments WHERE id = ?",
            (comment_id,),
        ).fetchone()
        return self._row_to_dict(row)

    def get_by_name(self, username):
        self._validate_name(username)
        rows = self._connection.execute(
            "SELECT id, name, message FROM comments WHERE name = ? ORDER BY id",
            (username,),
        ).fetchall()
        return [dict(row) for row in rows]

    def add(self, comment_id, username, message):
        self._validate_id(comment_id)
        self._validate_name(username)
        self._validate_message(message)
        try:
            with self._connection:
                self._connection.execute(
                    "INSERT INTO comments (id, name, message) VALUES (?, ?, ?)",
                    (comment_id, username, message),
                )
        except sqlite3.IntegrityError as error:
            raise DuplicateIdError(f"запись с id={comment_id} уже существует") from error
        return True

    def update(self, comment_id, new_message):
        self._validate_id(comment_id)
        self._validate_message(new_message)
        with self._connection:
            cursor = self._connection.execute(
                "UPDATE comments SET message = ? WHERE id = ?",
                (new_message, comment_id),
            )
        if cursor.rowcount == 0:
            raise RecordNotFoundError(f"запись с id={comment_id} не найдена")
        return True

    def delete(self, comment_id):
        self._validate_id(comment_id)
        with self._connection:
            cursor = self._connection.execute(
                "DELETE FROM comments WHERE id = ?",
                (comment_id,),
            )
        return cursor.rowcount > 0

    def close(self):
        self._connection.close()
