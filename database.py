import sqlite3
import logging
from typing import Any, Callable, List

class ProblemDatabase:
    def __init__(self, db_path: str = "problems.db"):
        self.db_path = db_path
        self._callbacks: List[Callable[[], None]] = []

    def init_db(self) -> None:
        logging.info("Initializing database...")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS problems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    grp TEXT,
                    url TEXT,
                    slug TEXT UNIQUE,
                    solved INTEGER DEFAULT 0,
                    time_spent INTEGER DEFAULT 0,
                    save_note_on_solve INTEGER DEFAULT 0,
                    note_path TEXT
                )
                '''
            )
            cursor = conn.execute("SELECT COUNT(*) FROM problems")
            count = cursor.fetchone()[0]
        logging.info(f"Database initialized. Found {count} problems")

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called on database updates."""
        self._callbacks.append(callback)

    def _trigger_callbacks(self) -> None:
        """Trigger all registered callbacks."""
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                logging.error(f"Error in callback: {e}")

    def create_problem(self, name: str, grp: str, url: str, slug: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO problems (name, grp, url, slug) VALUES (?, ?, ?, ?)",
                (name, grp, url, slug)
            )
        self._trigger_callbacks()

    def save_problem(self, name: str, grp: str, url: str, slug: str, solved: int = 0, save_note_on_solve: int = 0, note_path: str="") -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id FROM problems WHERE slug = ?",
                (slug,)
            )
            if cursor.fetchone():
                conn.execute(
                    "UPDATE problems SET name = ?, grp = ?, url = ?, solved = ?, save_note_on_solve = ?, note_path = ? WHERE slug = ?",
                    (name, grp, url, solved, save_note_on_solve, note_path, slug )
                )
            else:
                conn.execute(
                    "INSERT INTO problems (name, grp, url, slug, solved, save_note_on_solve, note_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (name, grp, url, slug, solved, save_note_on_solve, note_path)
                )
        self._trigger_callbacks()

    def load_problems(self, filters: dict[str, Any] = None) -> list[tuple]:
        filters = filters or {}
        sql = "SELECT id, name, grp, solved FROM problems"
        clauses = []
        params = []
        for key, value in filters.items():
            if key == "solved":
                clauses.append("solved = ?")
                params.append(1 if value else 0)
            elif key == "name_like":
                clauses.append("name LIKE ?")
                params.append(f"%{value}%")
            else:
                clauses.append(f"{key} = ?")
                params.append(value)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id DESC"
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(sql, params).fetchall()

    def get_problem(self, problem_id: int) -> tuple | None:
        """
        Return (slug, name, solved, save_note_on_solve) for the given problem ID, or None if not found.
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT slug, name, solved, save_note_on_solve FROM problems WHERE id = ?",
                (problem_id,)
            ).fetchone()
            return row if row else None

    def update_problem(self, slug: str, **fields) -> None:
        if not fields:
            return
        cols = []
        vals = []
        for key, value in fields.items():
            cols.append(f"{key} = ?")
            vals.append(value)
        vals.append(slug)
        sql = f"UPDATE problems SET {', '.join(cols)} WHERE slug = ?"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(sql, vals)

    def delete_problem(self, slug: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM problems WHERE slug = ?",
                (slug,)
            )
        self._trigger_callbacks()

    def get_url(self, slug: str) -> str | None:
        """
        Return the URL for the given problem slug, or None if not found.
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT url FROM problems WHERE slug = ?",
                (slug,)
            ).fetchone()
            return row[0] if row else None

    def get_save_note_on_solve(self, slug: str) -> int:
        """
        Return the save_note_on_solve flag for the given problem slug.
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT save_note_on_solve FROM problems WHERE slug = ?",
                (slug,)
            ).fetchone()
            return row[0] if row else 0
        self._trigger_callbacks()

    def mark_solved(self, slug: str) -> None:
        """
        Mark the problem as solved by setting solved=1.
        """
        self.update_problem(slug, solved=1)
        self._trigger_callbacks()

    def increment_time_spent(self, slug: str, seconds: int) -> None:
        """
        Increment the time spent on a problem by a given number of seconds.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE problems SET time_spent = time_spent + ? WHERE slug = ?",
                (seconds, slug)
            )
        self._trigger_callbacks()

    def get_time_spent(self, slug: str) -> int:
        """
        Retrieve the time spent on a problem.
        """
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT time_spent FROM problems WHERE slug = ?",
                (slug,)
            ).fetchone()
            return row[0] if row else 0

    def update_time_spent(self, slug: str, time_spent: int) -> None:
        """
        Update the time spent on a problem by setting it to a specific value.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE problems SET time_spent = ? WHERE slug = ?",
                (time_spent, slug)
            )
        self._trigger_callbacks()




