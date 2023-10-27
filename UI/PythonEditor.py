import math

from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget
from PySide6.QtGui import QTextOption, QGuiApplication, Qt, QTextCursor, QColor, QTextFormat, QPaintEvent, QPainter, \
    QSyntaxHighlighter, QTextCharFormat, QFont, QPalette, QBrush
from PySide6.QtCore import QRect, QRegularExpression, QSize


class PythonEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.lineNumberDisplayer = LineNumberDisplayerProxy(self)
        self.blockCountChanged.connect(self.OnLineCountChanged)
        self.cursorPositionChanged.connect(self.OnCursorMoved)
        self.updateRequest.connect(self.OnScrolled)

        self.highlighter = SyntaxHighlighter(self.document())

        self.setStyleSheet("""
        background-color: rgb(40, 40, 40);
        border: none;
        color: white;
        font-family: "Consolas";
        selection-background-color: rgb(60, 60, 60);
        """)
        self.OnLineCountChanged()
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)

        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Highlight, QColor(255, 255, 255, 30))
        palette.setBrush(QPalette.ColorRole.HighlightedText, QBrush(Qt.BrushStyle.NoBrush))
        self.setPalette(palette)

    def keyPressEvent(self, e) -> None:
        controlPressed = bool(QGuiApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)
        if e.key() == Qt.Key.Key_Tab:
            if self.textCursor().hasSelection():
                self.IndentSelection(1)
            else:
                self.textCursor().insertText("    ")
        elif e.key() == Qt.Key.Key_Backtab:
            self.IndentSelection(-1)
        elif e.key() == Qt.Key.Key_Backspace:
            if not self.textCursor().hasSelection():
                lineStart = self.textCursor().block().position()
                cursorPos = self.textCursor().position()
                text = self.toPlainText()[lineStart:cursorPos]
                if all([x == " " for x in text]):
                    leadingSpaces = max(0, len(text) - 4)
                    leadingSpaces = math.ceil(leadingSpaces / 4) * 4
                    delta = len(text) - leadingSpaces
                    delPos = cursorPos - delta
                    cursor = self.textCursor()
                    cursor.setPosition(delPos, QTextCursor.MoveMode.KeepAnchor)
                    cursor.removeSelectedText()
                else:
                    super().keyPressEvent(e)
            else:
                super().keyPressEvent(e)
        else:
            super().keyPressEvent(e)
        if e.key() == Qt.Key.Key_Equal and controlPressed:
            self.zoomIn(1)
        elif e.key() == Qt.Key.Key_Minus and controlPressed:
            self.zoomOut(1)
        self.OnLineCountChanged()

    def IndentSelection(self, direction):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        cursor.setPosition(start)
        blockStart = cursor.block().position()
        cursor.setPosition(end)
        blockEnd = cursor.block().position() + cursor.block().length() - 2
        cursor.setPosition(blockStart, QTextCursor.MoveMode.MoveAnchor)
        cursor.setPosition(blockEnd, QTextCursor.MoveMode.KeepAnchor)

        selectedText = self.toPlainText()[blockStart:blockEnd]
        indented = []
        delta = 0
        for line in selectedText.splitlines():
            if len(line.lstrip()) > 0:
                leadingSpaces = len(line) - len(line.lstrip())
                old = leadingSpaces
                leadingSpaces = max(0, leadingSpaces + direction * 4)
                f = math.ceil if direction < 0 else math.floor
                leadingSpaces = f(leadingSpaces / 4) * 4
                delta += leadingSpaces - old
                indented.append(" " * leadingSpaces + line.lstrip())
            else:
                indented.append(line)
        indented = "\n".join(indented)

        cursor.insertText(indented)

        blockEnd += delta

        cursor = self.textCursor()
        cursor.setPosition(blockStart, QTextCursor.MoveMode.MoveAnchor)
        cursor.setPosition(blockEnd, QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(cursor)

    def OnLineCountChanged(self):
        self.setViewportMargins(self.LineNumberWidth(), 0, 0, 0)
        self.lineNumberDisplayer.update()

    def OnScrolled(self, rect: QRect, dy: int):
        self.lineNumberDisplayer.scroll(0, dy)

    def OnCursorMoved(self):
        self.lineNumberDisplayer.update()

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        cr = self.contentsRect()
        self.lineNumberDisplayer.setGeometry(QRect(cr.left(),
                                                   cr.top(),
                                                   self.LineNumberWidth(),
                                                   cr.height()))

    def PaintLineNumbers(self, event: QPaintEvent):
        painter = QPainter(self.lineNumberDisplayer)
        painter.fillRect(event.rect(), QColor(50, 50, 50))
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        blockGeometry = self.blockBoundingGeometry(block)
        blockHeight = round(blockGeometry.height())
        top = round(blockGeometry.translated(self.contentOffset()).top())
        bottom = top + blockHeight

        activeNumber = self.textCursor().blockNumber()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                if blockNumber == activeNumber:
                    painter.fillRect(0,
                                     top,
                                     self.lineNumberDisplayer.width(),
                                     self.fontMetrics().height(), QColor(60, 60, 60))
                painter.setPen(QColor(230, 230, 230) if blockNumber == activeNumber else QColor(180, 180, 180))
                painter.setFont(self.font())
                painter.drawText(0,
                                 top,
                                 self.lineNumberDisplayer.width() - 5,
                                 self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, number)
            block = block.next()
            top = bottom
            bottom = top + blockHeight
            blockNumber += 1

    def LineNumberWidth(self) -> int:
        digits = math.ceil(math.log10(self.blockCount() + 1))
        return 15 + self.fontMetrics().horizontalAdvance("9") * digits


class SyntaxHighlighter(QSyntaxHighlighter):
    class HighlighterRule:
        def __init__(self, pattern: QRegularExpression, ruleFormat: QTextCharFormat):
            self.pattern = pattern
            self.format = ruleFormat

    def __init__(self, parent):
        import keyword
        def KeywordMatch(x: str):
            return r"(?:\s|^)(" + x + ")(?:\s|$)"

        super().__init__(parent)

        self.rules = []

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(255, 0, 100))
        keywordFormat.setFontWeight(QFont.Weight.Bold)
        keywordPatterns = [KeywordMatch(kw) for kw in keyword.kwlist]

        for pattern in keywordPatterns:
            self.rules.append(SyntaxHighlighter.HighlighterRule(QRegularExpression(pattern), keywordFormat))

        defFormat = QTextCharFormat()
        defFormat.setForeground(QColor(0, 200, 255))
        defFormat.setFontItalic(True)
        self.rules.append(SyntaxHighlighter.HighlighterRule(QRegularExpression(KeywordMatch("def")), defFormat))
        self.rules.append(SyntaxHighlighter.HighlighterRule(QRegularExpression(KeywordMatch("class")), defFormat))

        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor(0, 255, 100))
        self.rules.append(SyntaxHighlighter.HighlighterRule(QRegularExpression(r"\""), stringFormat))

        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor(150, 150, 150))
        self.rules.append(SyntaxHighlighter.HighlighterRule(QRegularExpression(r"#.*"), commentFormat))

    def highlightBlock(self, text) -> None:
        for rule in self.rules:
            matchIterator = rule.pattern.globalMatch(text)
            while matchIterator.hasNext():
                match = matchIterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), rule.format)


class LineNumberDisplayerProxy(QWidget):
    def __init__(self, editor: PythonEditor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.LineNumberWidth(), 0)

    def paintEvent(self, event) -> None:
        return self.editor.PaintLineNumbers(event)
