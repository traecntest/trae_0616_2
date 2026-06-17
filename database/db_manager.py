import sqlite3
import os
from typing import Optional, List, Tuple, Any


class DatabaseManager:
    _instance = None

    def __init__(self):
        self._connections = {}
        self._current_db: Optional[str] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self, db_path: str) -> bool:
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            self._connections[db_path] = conn
            self._current_db = db_path
            return True
        except sqlite3.Error:
            return False

    def disconnect(self, db_path: str) -> None:
        if db_path in self._connections:
            self._connections[db_path].close()
            del self._connections[db_path]
            if self._current_db == db_path:
                self._current_db = None

    def get_connection(self, db_path: Optional[str] = None) -> Optional[sqlite3.Connection]:
        path = db_path or self._current_db
        return self._connections.get(path)

    def set_current_db(self, db_path: str) -> None:
        if db_path in self._connections:
            self._current_db = db_path

    def get_current_db(self) -> Optional[str]:
        return self._current_db

    def get_tables(self, db_path: Optional[str] = None) -> List[str]:
        conn = self.get_connection(db_path)
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def get_table_columns(self, table_name: str, db_path: Optional[str] = None) -> List[Tuple[str, str]]:
        conn = self.get_connection(db_path)
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            return [(row[1], row[2]) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    def get_row_count(self, table_name: str, db_path: Optional[str] = None) -> int:
        conn = self.get_connection(db_path)
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
            return cursor.fetchone()[0]
        except sqlite3.Error:
            return 0

    def execute_query(self, sql: str, db_path: Optional[str] = None) -> Tuple[List[Any], List[str]]:
        conn = self.get_connection(db_path)
        if not conn:
            raise RuntimeError("No database connection")

        cursor = conn.cursor()
        cursor.execute(sql)

        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = [list(row) for row in cursor.fetchall()]
            return rows, columns
        else:
            conn.commit()
            return [], []

    def execute_many(self, sql: str, data: List[tuple], db_path: Optional[str] = None) -> int:
        conn = self.get_connection(db_path)
        if not conn:
            raise RuntimeError("No database connection")

        cursor = conn.cursor()
        cursor.executemany(sql, data)
        conn.commit()
        return cursor.rowcount

    def fetch_page(self, table_name: str, offset: int, limit: int,
                   db_path: Optional[str] = None) -> Tuple[List[Any], List[str]]:
        conn = self.get_connection(db_path)
        if not conn:
            return [], []

        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM '{table_name}' LIMIT ? OFFSET ?", (limit, offset))
        columns = [desc[0] for desc in cursor.description]
        rows = [list(row) for row in cursor.fetchall()]
        return rows, columns

    def is_connected(self, db_path: Optional[str] = None) -> bool:
        path = db_path or self._current_db
        return path in self._connections
