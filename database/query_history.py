import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional


class QueryHistory:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            app_data = os.path.join(os.path.expanduser("~"), ".sqlite_manager")
            os.makedirs(app_data, exist_ok=True)
            db_path = os.path.join(app_data, "history.db")
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        return self._conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sql_text TEXT NOT NULL,
                database_path TEXT,
                execution_time REAL,
                row_count INTEGER,
                success INTEGER,
                error_message TEXT,
                created_at TEXT NOT NULL,
                favorite INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

    def add_record(self, sql_text: str, database_path: str = "",
                   execution_time: float = 0.0, row_count: int = 0,
                   success: bool = True, error_message: str = "") -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO query_history (sql_text, database_path, execution_time,
                                       row_count, success, error_message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (sql_text, database_path, execution_time, row_count,
              1 if success else 0, error_message, created_at))
        record_id = cursor.lastrowid
        conn.commit()
        return record_id

    def get_history(self, limit: int = 100, offset: int = 0,
                    keyword: str = "") -> List[Dict]:
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if keyword:
            cursor.execute('''
                SELECT * FROM query_history
                WHERE sql_text LIKE ?
                ORDER BY created_at DESC LIMIT ? OFFSET ?
            ''', (f"%{keyword}%", limit, offset))
        else:
            cursor.execute('''
                SELECT * FROM query_history
                ORDER BY created_at DESC LIMIT ? OFFSET ?
            ''', (limit, offset))

        rows = [dict(row) for row in cursor.fetchall()]
        return rows

    def get_favorites(self) -> List[Dict]:
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM query_history WHERE favorite = 1
            ORDER BY created_at DESC
        ''')
        rows = [dict(row) for row in cursor.fetchall()]
        return rows

    def toggle_favorite(self, record_id: int) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT favorite FROM query_history WHERE id = ?', (record_id,))
        row = cursor.fetchone()
        if not row:
            return False
        new_val = 0 if row[0] else 1
        cursor.execute('UPDATE query_history SET favorite = ? WHERE id = ?',
                       (new_val, record_id))
        conn.commit()
        return True

    def delete_record(self, record_id: int) -> bool:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM query_history WHERE id = ?', (record_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted

    def clear_all(self) -> None:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM query_history')
        conn.commit()

    def get_count(self, keyword: str = "") -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        if keyword:
            cursor.execute('SELECT COUNT(*) FROM query_history WHERE sql_text LIKE ?',
                           (f"%{keyword}%",))
        else:
            cursor.execute('SELECT COUNT(*) FROM query_history')
        count = cursor.fetchone()[0]
        return count

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
