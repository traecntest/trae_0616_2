from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, Signal
from PySide6.QtWidgets import QTableView, QHeaderView, QAbstractItemView
from typing import List, Any, Optional
import sqlite3
from database import DatabaseManager


class VirtualTableModel(QAbstractTableModel):
    data_loaded = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._columns: List[str] = []
        self._row_count: int = 0
        self._page_size: int = 200
        self._cache: dict = {}
        self._table_name: Optional[str] = None
        self._db_path: Optional[str] = None
        self._static_data: List[List[Any]] = []
        self._use_static_data: bool = True

    def set_static_data(self, rows: List[List[Any]], columns: List[str]) -> None:
        self.beginResetModel()
        self._columns = columns
        self._static_data = rows
        self._row_count = len(rows)
        self._use_static_data = True
        self._cache.clear()
        self.endResetModel()
        self.data_loaded.emit()

    def set_table(self, table_name: str, db_path: Optional[str] = None) -> None:
        db = DatabaseManager()
        self._table_name = table_name
        self._db_path = db_path or db.get_current_db()
        self._use_static_data = False
        self._cache.clear()

        self._row_count = db.get_row_count(table_name, self._db_path)
        columns_info = db.get_table_columns(table_name, self._db_path)
        self._columns = [col[0] for col in columns_info]

        self.beginResetModel()
        self.endResetModel()
        self.data_loaded.emit()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return self._row_count

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._columns)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        row = index.row()
        col = index.column()

        if row < 0 or row >= self._row_count:
            return None

        if self._use_static_data:
            if row < len(self._static_data) and col < len(self._columns):
                return str(self._static_data[row][col])
            return ""

        page = row // self._page_size
        offset = row % self._page_size

        if page not in self._cache:
            self._load_page(page)

        if page in self._cache and offset < len(self._cache[page]):
            row_data = self._cache[page][offset]
            if col < len(row_data):
                return str(row_data[col])

        return ""

    def _load_page(self, page: int) -> None:
        db = DatabaseManager()
        if not self._table_name:
            return

        try:
            conn = db.get_connection(self._db_path)
            if not conn:
                return

            offset = page * self._page_size
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM '{self._table_name}' LIMIT ? OFFSET ?",
                (self._page_size, offset)
            )
            rows = [list(row) for row in cursor.fetchall()]
            self._cache[page] = rows

            if len(self._cache) > 50:
                oldest = min(self._cache.keys())
                del self._cache[oldest]

        except sqlite3.Error:
            pass

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            if section < len(self._columns):
                return self._columns[section]
            return f"Column {section + 1}"
        else:
            return str(section + 1)

    @property
    def columns(self) -> List[str]:
        return self._columns

    @property
    def total_rows(self) -> int:
        return self._row_count

    def clear(self) -> None:
        self.beginResetModel()
        self._columns = []
        self._row_count = 0
        self._cache.clear()
        self._static_data = []
        self._use_static_data = True
        self._table_name = None
        self.endResetModel()


class VirtualTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._model = VirtualTableModel(self)
        self.setModel(self._model)

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(False)

        self.verticalHeader().setDefaultSectionSize(25)
        self.setShowGrid(True)

    def set_static_data(self, rows: list, columns: list) -> None:
        self._model.set_static_data(rows, columns)
        self.resizeColumnsToContents()
        self._adjust_column_widths()

    def set_table(self, table_name: str, db_path: str = None) -> None:
        self._model.set_table(table_name, db_path)
        self.resizeColumnsToContents()
        self._adjust_column_widths()

    def _adjust_column_widths(self) -> None:
        header = self.horizontalHeader()
        for i in range(header.count()):
            if header.sectionSize(i) > 300:
                header.resizeSection(i, 300)
            elif header.sectionSize(i) < 80:
                header.resizeSection(i, 80)

    def clear(self) -> None:
        self._model.clear()

    @property
    def total_rows(self) -> int:
        return self._model.total_rows

    @property
    def columns(self) -> list:
        return self._model.columns
