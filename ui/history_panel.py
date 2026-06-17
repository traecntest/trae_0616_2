from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QLabel, QSplitter, QTextEdit, QMenu, QInputDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QFont
from typing import Optional
from database import QueryHistory


class HistoryPanel(QWidget):
    sql_selected = Signal(str)
    sql_executed = Signal(str)

    def __init__(self, history: QueryHistory, parent=None):
        super().__init__(parent)
        self._history = history
        self._current_records = []
        self._page_size = 50
        self._offset = 0
        self._keyword = ""

        self._init_ui()
        self.load_history()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索历史记录...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)

        layout.addLayout(search_layout)

        splitter = QSplitter(Qt.Vertical)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._on_context_menu)
        splitter.addWidget(self.list_widget)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setFont(QFont("Consolas", 9))
        splitter.addWidget(self.detail_text)

        splitter.setSizes([200, 100])
        layout.addWidget(splitter)

        btn_layout = QHBoxLayout()
        self.prev_btn = QPushButton("上一页")
        self.prev_btn.clicked.connect(self._load_prev)
        btn_layout.addWidget(self.prev_btn)

        self.page_label = QLabel("第 1 页")
        self.page_label.setAlignment(Qt.AlignCenter)
        btn_layout.addWidget(self.page_label)

        self.next_btn = QPushButton("下一页")
        self.next_btn.clicked.connect(self._load_next)
        btn_layout.addWidget(self.next_btn)

        layout.addLayout(btn_layout)

        self.count_label = QLabel("共 0 条记录")
        self.count_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.count_label)

    def load_history(self) -> None:
        self._current_records = self._history.get_history(
            limit=self._page_size,
            offset=self._offset,
            keyword=self._keyword
        )

        self.list_widget.clear()
        for record in self._current_records:
            item = QListWidgetItem()
            sql_preview = record['sql_text'][:80].replace('\n', ' ')
            if len(record['sql_text']) > 80:
                sql_preview += "..."

            time_str = record['created_at']
            success = bool(record['success'])

            if success:
                status_text = f"✓ {record['row_count']}行 {record['execution_time']:.2f}s"
                item.setForeground(QBrush(QColor("#228b22")))
            else:
                status_text = "✗ 执行失败"
                item.setForeground(QBrush(QColor("#dc143c")))

            item.setText(f"{time_str}\n{sql_preview}\n{status_text}")
            item.setData(Qt.UserRole, record)
            self.list_widget.addItem(item)

        total = self._history.get_count(self._keyword)
        self.count_label.setText(f"共 {total} 条记录")

        current_page = (self._offset // self._page_size) + 1
        total_pages = max(1, (total + self._page_size - 1) // self._page_size)
        self.page_label.setText(f"第 {current_page} / {total_pages} 页")

        self.prev_btn.setEnabled(self._offset > 0)
        self.next_btn.setEnabled(self._offset + self._page_size < total)

    def _on_search(self, text: str) -> None:
        self._keyword = text
        self._offset = 0
        self.load_history()

    def _load_prev(self) -> None:
        if self._offset >= self._page_size:
            self._offset -= self._page_size
            self.load_history()

    def _load_next(self) -> None:
        total = self._history.get_count(self._keyword)
        if self._offset + self._page_size < total:
            self._offset += self._page_size
            self.load_history()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        record = item.data(Qt.UserRole)
        if record:
            detail = f"时间: {record['created_at']}\n"
            detail += f"数据库: {record['database_path'] or '未指定'}\n"
            detail += f"结果: {'成功' if record['success'] else '失败'}\n"
            detail += f"行数: {record['row_count']}\n"
            detail += f"耗时: {record['execution_time']:.4f} 秒\n"
            if record['error_message']:
                detail += f"错误: {record['error_message']}\n"
            detail += f"\n--- SQL ---\n{record['sql_text']}"
            self.detail_text.setText(detail)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        record = item.data(Qt.UserRole)
        if record:
            self.sql_executed.emit(record['sql_text'])

    def _on_context_menu(self, pos) -> None:
        item = self.list_widget.itemAt(pos)
        if not item:
            return

        record = item.data(Qt.UserRole)
        menu = QMenu(self)

        insert_action = QAction("插入到编辑器", self)
        insert_action.triggered.connect(lambda: self.sql_selected.emit(record['sql_text']))
        menu.addAction(insert_action)

        execute_action = QAction("执行", self)
        execute_action.triggered.connect(lambda: self.sql_executed.emit(record['sql_text']))
        menu.addAction(execute_action)

        menu.addSeparator()

        favorite_action = QAction("收藏/取消收藏", self)
        favorite_action.triggered.connect(
            lambda: self._toggle_favorite(record['id'])
        )
        menu.addAction(favorite_action)

        delete_action = QAction("删除", self)
        delete_action.triggered.connect(
            lambda: self._delete_record(record['id'])
        )
        menu.addAction(delete_action)

        menu.exec_(self.list_widget.mapToGlobal(pos))

    def _toggle_favorite(self, record_id: int) -> None:
        self._history.toggle_favorite(record_id)
        self.load_history()

    def _delete_record(self, record_id: int) -> None:
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这条历史记录吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._history.delete_record(record_id)
            self.load_history()

    def refresh(self) -> None:
        self.load_history()
