import sqlite3


class TriangleDatabase:
    def __init__(self, path=":memory:"):
        self._connection = sqlite3.connect(path)
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS triangles ("
            "side1 REAL NOT NULL, "
            "side2 REAL NOT NULL, "
            "side3 REAL NOT NULL, "
            "triangle_type TEXT, "
            "error_message TEXT, "
            "PRIMARY KEY (side1, side2, side3))"
        )
        self._connection.commit()

    def add(self, a, b, c, triangle_type, error_message):
        self._connection.execute(
            "INSERT OR REPLACE INTO triangles VALUES (?, ?, ?, ?, ?)",
            (a, b, c, triangle_type, error_message),
        )
        self._connection.commit()

    def get(self, a, b, c):
        cursor = self._connection.execute(
            "SELECT triangle_type, error_message FROM triangles "
            "WHERE side1 = ? AND side2 = ? AND side3 = ?",
            (a, b, c),
        )
        return cursor.fetchone()

    def delete(self, a, b, c):
        cursor = self._connection.execute(
            "DELETE FROM triangles WHERE side1 = ? AND side2 = ? AND side3 = ?",
            (a, b, c),
        )
        self._connection.commit()
        return cursor.rowcount > 0

    def close(self):
        self._connection.close()
