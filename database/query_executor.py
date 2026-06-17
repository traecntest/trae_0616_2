import time
import sqlite3
from typing import List, Any, Tuple, Optional, Callable
from PySide6.QtCore import QThread, Signal
from .db_manager import DatabaseManager
from .query_history import QueryHistory


class QueryWorker(QThread):
    finished_signal = Signal(list, list, float, int, bool, str)
    error_signal = Signal(str)

    def __init__(self, sql: str, db_path: Optional[str] = None,
                 history: Optional[QueryHistory] = None):
        super().__init__()
        self._sql = sql
        self._db_path = db_path
        self._history = history
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        start_time = time.time()
        thread_conn = None
        try:
            db = DatabaseManager()
            db_path = self._db_path or db.get_current_db()

            if not db_path:
                self.error_signal.emit("No database selected")
                return

            thread_conn = sqlite3.connect(db_path)
            thread_conn.row_factory = sqlite3.Row

            cursor = thread_conn.cursor()
            cursor.execute(self._sql)

            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = [list(row) for row in cursor.fetchall()]
                row_count = len(rows)
                success = True
                error_msg = ""
            else:
                thread_conn.commit()
                rows = []
                columns = []
                row_count = cursor.rowcount
                success = True
                error_msg = ""

            elapsed = time.time() - start_time

            if self._history:
                try:
                    self._history.add_record(
                        sql_text=self._sql,
                        database_path=db_path or "",
                        execution_time=elapsed,
                        row_count=row_count,
                        success=success,
                        error_message=error_msg
                    )
                except Exception:
                    pass

            self.finished_signal.emit(rows, columns, elapsed, row_count, success, error_msg)

        except sqlite3.Error as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            if self._history:
                try:
                    self._history.add_record(
                        sql_text=self._sql,
                        database_path=self._db_path or "",
                        execution_time=elapsed,
                        row_count=0,
                        success=False,
                        error_message=error_msg
                    )
                except Exception:
                    pass
            self.error_signal.emit(error_msg)
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"Unexpected error: {str(e)}"
            if self._history:
                try:
                    self._history.add_record(
                        sql_text=self._sql,
                        database_path=self._db_path or "",
                        execution_time=elapsed,
                        row_count=0,
                        success=False,
                        error_message=error_msg
                    )
                except Exception:
                    pass
            self.error_signal.emit(error_msg)
        finally:
            if thread_conn:
                try:
                    thread_conn.close()
                except Exception:
                    pass


class QueryExecutor:
    def __init__(self, history: Optional[QueryHistory] = None):
        self._history = history or QueryHistory()
        self._worker: Optional[QueryWorker] = None
        self._result_callbacks: List[Callable] = []
        self._error_callbacks: List[Callable] = []

    @property
    def history(self) -> QueryHistory:
        return self._history

    def execute_async(self, sql: str, db_path: Optional[str] = None,
                      on_result: Optional[Callable] = None,
                      on_error: Optional[Callable] = None) -> None:
        self._worker = QueryWorker(sql, db_path, self._history)

        if on_result:
            self._worker.finished_signal.connect(on_result)
        if on_error:
            self._worker.error_signal.connect(on_error)

        self._worker.start()

    def execute_sync(self, sql: str, db_path: Optional[str] = None) -> Tuple[List[Any], List[str], float, int]:
        db = DatabaseManager()
        start_time = time.time()

        conn = db.get_connection(db_path)
        if not conn:
            raise RuntimeError("No database connection")

        cursor = conn.cursor()
        cursor.execute(sql)

        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = [list(row) for row in cursor.fetchall()]
            row_count = len(rows)
        else:
            conn.commit()
            rows = []
            columns = []
            row_count = cursor.rowcount

        elapsed = time.time() - start_time

        self._history.add_record(
            sql_text=sql,
            database_path=db_path or db.get_current_db() or "",
            execution_time=elapsed,
            row_count=row_count,
            success=True,
            error_message=""
        )

        return rows, columns, elapsed, row_count

    def is_running(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def cancel(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()
