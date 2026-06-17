from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QToolBar, QStatusBar, QLabel, QMessageBox, QFileDialog,
    QTabWidget, QPushButton, QSpinBox, QLineEdit, QComboBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon, QKeySequence
from typing import Optional
import os

from database import DatabaseManager, QueryHistory, QueryExecutor
from ui import VirtualTableView, SqlEditor, DatabaseTreeWidget, HistoryPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SQLite 数据库管理工具")
        self.resize(1200, 800)

        self._db = DatabaseManager()
        self._history = QueryHistory()
        self._executor = QueryExecutor(self._history)

        self._init_ui()
        self._init_toolbar()
        self._init_statusbar()

    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)

        self._db_tree = DatabaseTreeWidget()
        self._db_tree.table_double_clicked.connect(self._on_table_double_clicked)
        self._db_tree.table_selected.connect(self._on_table_selected)
        left_layout.addWidget(QLabel("数据库结构"))
        left_layout.addWidget(self._db_tree)

        main_splitter.addWidget(left_panel)

        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(5, 5, 5, 5)
        center_layout.setSpacing(5)

        center_layout.addWidget(QLabel("SQL 编辑器"))

        self._sql_editor = SqlEditor()
        center_layout.addWidget(self._sql_editor, 2)

        btn_layout = QHBoxLayout()
        self._execute_btn = QPushButton("执行 (Ctrl+Enter)")
        self._execute_btn.clicked.connect(self.execute_sql)
        btn_layout.addWidget(self._execute_btn)

        self._explain_btn = QPushButton("解释执行")
        self._explain_btn.clicked.connect(self._execute_explain)
        btn_layout.addWidget(self._explain_btn)

        btn_layout.addStretch()

        self._clear_btn = QPushButton("清空编辑器")
        self._clear_btn.clicked.connect(self._clear_editor)
        btn_layout.addWidget(self._clear_btn)

        center_layout.addLayout(btn_layout)

        center_layout.addWidget(QLabel("查询结果"))

        self._result_tabs = QTabWidget()

        self._result_table = VirtualTableView()
        self._result_tabs.addTab(self._result_table, "结果")

        self._message_text = QLineEdit()
        self._message_text.setReadOnly(True)
        self._result_tabs.addTab(self._message_widget(), "消息")

        center_layout.addWidget(self._result_tabs, 3)

        main_splitter.addWidget(center_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)

        right_layout.addWidget(QLabel("查询历史"))
        self._history_panel = HistoryPanel(self._history)
        self._history_panel.sql_selected.connect(self._insert_sql_to_editor)
        self._history_panel.sql_executed.connect(self._execute_sql_from_history)
        right_layout.addWidget(self._history_panel)

        main_splitter.addWidget(right_panel)

        main_splitter.setSizes([200, 700, 300])
        main_layout.addWidget(main_splitter)

    def _message_widget(self) -> QWidget:
        from PySide6.QtWidgets import QTextEdit
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self._msg_text = QTextEdit()
        self._msg_text.setReadOnly(True)
        layout.addWidget(self._msg_text)
        return widget

    def _init_toolbar(self) -> None:
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        open_action = QAction("打开数据库", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_database)
        toolbar.addAction(open_action)

        new_action = QAction("新建数据库", self)
        new_action.triggered.connect(self._new_database)
        toolbar.addAction(new_action)

        close_action = QAction("关闭数据库", self)
        close_action.triggered.connect(self._close_database)
        toolbar.addAction(close_action)

        toolbar.addSeparator()

        refresh_action = QAction("刷新", self)
        refresh_action.setShortcut(QKeySequence.Refresh)
        refresh_action.triggered.connect(self._refresh)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        self._status_label = QLabel("未连接")
        toolbar.addWidget(self._status_label)

    def _init_statusbar(self) -> None:
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        self._row_count_label = QLabel("行数: 0")
        self._status_bar.addPermanentWidget(self._row_count_label)

        self._time_label = QLabel("耗时: 0ms")
        self._status_bar.addPermanentWidget(self._time_label)

    def _open_database(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开 SQLite 数据库", "",
            "SQLite 数据库 (*.db *.sqlite *.db3 *.sqlite3);;所有文件 (*.*)"
        )
        if file_path:
            if self._db.connect(file_path):
                self._db.set_current_db(file_path)
                self._db_tree.refresh()
                self._update_status()
                self._status_bar.showMessage(f"已打开数据库: {file_path}", 3000)
            else:
                QMessageBox.critical(self, "错误", f"无法打开数据库: {file_path}")

    def _new_database(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "新建 SQLite 数据库", "database.db",
            "SQLite 数据库 (*.db *.sqlite)"
        )
        if file_path:
            if not file_path.endswith(('.db', '.sqlite', '.db3', '.sqlite3')):
                file_path += '.db'

            if self._db.connect(file_path):
                self._db.set_current_db(file_path)
                self._db_tree.refresh()
                self._update_status()
                self._status_bar.showMessage(f"已创建数据库: {file_path}", 3000)
            else:
                QMessageBox.critical(self, "错误", f"无法创建数据库: {file_path}")

    def _close_database(self) -> None:
        current_db = self._db.get_current_db()
        if current_db:
            self._db.disconnect(current_db)
            self._db_tree.refresh()
            self._result_table.clear()
            self._update_status()
            self._status_bar.showMessage("数据库已关闭", 3000)

    def _refresh(self) -> None:
        self._db_tree.refresh()
        self._history_panel.refresh()

    def _update_status(self) -> None:
        if self._db.is_connected():
            db_path = self._db.get_current_db()
            db_name = os.path.basename(db_path) if db_path else ""
            self._status_label.setText(f"已连接: {db_name}")
        else:
            self._status_label.setText("未连接")

    def execute_sql(self) -> None:
        sql = self._sql_editor.get_sql()
        if not sql:
            QMessageBox.warning(self, "提示", "请输入 SQL 语句")
            return

        if not self._db.is_connected():
            QMessageBox.warning(self, "提示", "请先打开数据库")
            return

        self._execute_btn.setEnabled(False)
        self._status_bar.showMessage("执行中...")

        self._executor.execute_async(
            sql,
            on_result=self._on_query_finished,
            on_error=self._on_query_error
        )

    def _execute_explain(self) -> None:
        sql = self._sql_editor.get_sql()
        if not sql:
            QMessageBox.warning(self, "提示", "请输入 SQL 语句")
            return
        explain_sql = f"EXPLAIN QUERY PLAN {sql}"
        self._sql_editor.set_sql(explain_sql)
        self.execute_sql()

    def _on_query_finished(self, rows, columns, elapsed, row_count, success, error_msg) -> None:
        self._execute_btn.setEnabled(True)
        self._time_label.setText(f"耗时: {elapsed*1000:.0f}ms")

        if columns and rows:
            self._result_table.set_static_data(rows, columns)
            self._row_count_label.setText(f"行数: {len(rows)}")
            self._result_tabs.setCurrentIndex(0)
        else:
            self._row_count_label.setText(f"影响行数: {row_count}")

        msg = f"执行成功\n耗时: {elapsed*1000:.2f} 毫秒\n"
        if columns:
            msg += f"返回 {len(rows)} 行, {len(columns)} 列\n"
        else:
            msg += f"影响 {row_count} 行\n"
        self._msg_text.setText(msg)

        self._status_bar.showMessage(f"执行完成，耗时 {elapsed*1000:.0f}ms", 3000)
        self._history_panel.refresh()

    def _on_query_error(self, error_msg: str) -> None:
        self._execute_btn.setEnabled(True)
        self._msg_text.setText(f"执行失败:\n{error_msg}")
        self._result_tabs.setCurrentIndex(1)
        self._status_bar.showMessage("执行失败", 3000)
        self._history_panel.refresh()

    def _on_table_double_clicked(self, table_name: str) -> None:
        sql = f"SELECT * FROM '{table_name}' LIMIT 100;"
        self._sql_editor.set_sql(sql)
        self.execute_sql()

    def _on_table_selected(self, table_name: str) -> None:
        pass

    def _clear_editor(self) -> None:
        self._sql_editor.set_sql("")

    def _insert_sql_to_editor(self, sql: str) -> None:
        self._sql_editor.set_sql(sql)

    def _execute_sql_from_history(self, sql: str) -> None:
        self._sql_editor.set_sql(sql)
        self.execute_sql()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.execute_sql()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        for db_path in list(self._db._connections.keys()):
            self._db.disconnect(db_path)
        event.accept()
