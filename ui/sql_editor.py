from PySide6.QtWidgets import QPlainTextEdit, QWidget
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QTextCursor
from PySide6.QtCore import Qt, Signal
import re


class SqlHighlighter(QSyntaxHighlighter):
    KEYWORDS = [
        'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN',
        'IS', 'NULL', 'ORDER', 'BY', 'ASC', 'DESC', 'GROUP', 'HAVING',
        'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE', 'CREATE',
        'TABLE', 'DROP', 'ALTER', 'ADD', 'COLUMN', 'PRIMARY', 'KEY', 'FOREIGN',
        'REFERENCES', 'UNIQUE', 'INDEX', 'VIEW', 'TRIGGER',
        'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER', 'JOIN', 'ON', 'AS',
        'UNION', 'ALL', 'DISTINCT', 'LIMIT', 'OFFSET', 'FETCH', 'FIRST',
        'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'ROUND', 'UPPER', 'LOWER',
        'INTEGER', 'TEXT', 'REAL', 'BLOB', 'NUMERIC', 'DEFAULT', 'AUTOINCREMENT',
        'BEGIN', 'COMMIT', 'ROLLBACK', 'TRANSACTION', 'PRAGMA', 'EXPLAIN',
        'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'WITH', 'RECURSIVE',
    ]

    def __init__(self, document):
        super().__init__(document)
        self._formats = {}
        self._setup_formats()
        self._rules = []
        self._setup_rules()

    def _setup_formats(self) -> None:
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keyword_format.setFontWeight(QFont.Bold)
        self._formats['keyword'] = keyword_format

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self._formats['string'] = string_format

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self._formats['number'] = number_format

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        comment_format.setFontItalic(True)
        self._formats['comment'] = comment_format

        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self._formats['function'] = function_format

        identifier_format = QTextCharFormat()
        identifier_format.setForeground(QColor("#9cdcfe"))
        self._formats['identifier'] = identifier_format

    def _setup_rules(self) -> None:
        for keyword in self.KEYWORDS:
            pattern = re.compile(rf'\b{keyword}\b', re.IGNORECASE)
            self._rules.append((pattern, self._formats['keyword']))

        self._rules.append((
            re.compile(r"'[^']*'"),
            self._formats['string']
        ))

        self._rules.append((
            re.compile(r'"[^"]*"'),
            self._formats['identifier']
        ))

        self._rules.append((
            re.compile(r'\b\d+\.?\d*\b'),
            self._formats['number']
        ))

        self._rules.append((
            re.compile(r'--.*'),
            self._formats['comment']
        ))

        self._rules.append((
            re.compile(r'/\*[\s\S]*?\*/'),
            self._formats['comment']
        ))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class SqlEditor(QPlainTextEdit):
    execute_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._highlighter = SqlHighlighter(self.document())

        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        self.setTabChangesFocus(False)
        self.setTabStopDistance(40)
        self.setPlaceholderText("输入 SQL 语句，按 Ctrl+Enter 执行...")

        self.setLineWrapMode(QPlainTextEdit.NoWrap)

    def get_sql(self) -> str:
        return self.toPlainText().strip()

    def set_sql(self, sql: str) -> None:
        self.setPlainText(sql)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and event.modifiers() == Qt.ControlModifier:
            self.execute_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)
