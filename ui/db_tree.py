from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon, QBrush, QColor
from typing import Optional
from database import DatabaseManager


class DatabaseTreeWidget(QTreeWidget):
    table_double_clicked = Signal(str)
    table_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["数据库对象"])
        self.setRootIsDecorated(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.itemClicked.connect(self._on_item_clicked)

        self._db_item: Optional[QTreeWidgetItem] = None

    def refresh(self) -> None:
        self.clear()
        db = DatabaseManager()
        current_db = db.get_current_db()

        if not current_db or not db.is_connected():
            no_conn_item = QTreeWidgetItem(["未连接数据库"])
            no_conn_item.setForeground(0, QBrush(QColor("#888888")))
            self.addTopLevelItem(no_conn_item)
            return

        import os
        db_name = os.path.basename(current_db)
        self._db_item = QTreeWidgetItem([db_name])
        self._db_item.setToolTip(0, current_db)
        self.addTopLevelItem(self._db_item)

        tables = db.get_tables()
        tables_item = QTreeWidgetItem(["表"])
        self._db_item.addChild(tables_item)

        for table_name in tables:
            table_item = QTreeWidgetItem([table_name])
            table_item.setData(0, Qt.UserRole, "table")
            table_item.setData(0, Qt.UserRole + 1, table_name)
            tables_item.addChild(table_item)

            columns = db.get_table_columns(table_name)
            for col_name, col_type in columns:
                col_item = QTreeWidgetItem([f"{col_name} ({col_type})"])
                col_item.setData(0, Qt.UserRole, "column")
                table_item.addChild(col_item)

        tables_item.setExpanded(True)
        self._db_item.setExpanded(True)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        item_type = item.data(0, Qt.UserRole)
        if item_type == "table":
            table_name = item.data(0, Qt.UserRole + 1)
            self.table_double_clicked.emit(table_name)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        item_type = item.data(0, Qt.UserRole)
        if item_type == "table":
            table_name = item.data(0, Qt.UserRole + 1)
            self.table_selected.emit(table_name)

    def _on_context_menu(self, pos) -> None:
        item = self.itemAt(pos)
        if not item:
            return

        item_type = item.data(0, Qt.UserRole)
        menu = QMenu(self)

        if item_type == "table":
            table_name = item.data(0, Qt.UserRole + 1)

            select_action = QAction("查询前100行", self)
            select_action.triggered.connect(lambda: self.table_double_clicked.emit(table_name))
            menu.addAction(select_action)

            copy_action = QAction("复制表名", self)
            copy_action.triggered.connect(
                lambda: self._copy_to_clipboard(table_name)
            )
            menu.addAction(copy_action)

            desc_action = QAction("复制查询语句", self)
            desc_action.triggered.connect(
                lambda: self._copy_to_clipboard(f"SELECT * FROM '{table_name}' LIMIT 100;")
            )
            menu.addAction(desc_action)

        menu.exec_(self.mapToGlobal(pos))

    def _copy_to_clipboard(self, text: str) -> None:
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
