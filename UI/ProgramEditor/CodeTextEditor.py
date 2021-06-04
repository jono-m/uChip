from PySide6.QtWidgets import QFrame, QTextEdit, QHBoxLayout
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, Qt, QBrush
from PySide6.QtCore import Signal, QRegularExpression
import keyword


class CodeTextEditor(QFrame):
    codeChanged = Signal()

    def __init__(self):
        super().__init__()

        self.textEdit = QTextEdit()
        self.textEdit.setTabStopDistance(20)
        self.textEdit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.textEdit.textChanged.connect(self.codeChanged.emit)

        self.textEdit.setAcceptRichText(False)

        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.textEdit)

        self._highlighter = PythonSyntaxHighlighter(self.textEdit.document())

    def SetCode(self, code: str):
        self.textEdit.setPlainText(code)

    def Code(self):
        return self.textEdit.toPlainText()


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        keywordFormat = QTextCharFormat()
        commentFormat = QTextCharFormat()
        stringFormat = QTextCharFormat()
        singleQuotedStringFormat = QTextCharFormat()

        self.highlightingRules = []

        # keyword
        brush = QBrush(Qt.blue, Qt.SolidPattern)
        keywordFormat.setForeground(brush)
        keywordFormat.setFontWeight(QFont.Bold)
        keywords = keyword.kwlist

        for word in keywords:
            pattern = QRegularExpression("\\b" + word + "\\b")
            rule = HighlightingRule(pattern, keywordFormat)
            self.highlightingRules.append(rule)

        # comment
        brush = QBrush(Qt.green, Qt.SolidPattern)
        pattern = QRegularExpression("#[^\n]*")
        commentFormat.setForeground(brush)
        rule = HighlightingRule(pattern, commentFormat)
        self.highlightingRules.append(rule)

        # string
        brush = QBrush(Qt.red, Qt.SolidPattern)
        pattern = QRegularExpression("\".*\"")
        stringFormat.setForeground(brush)
        rule = HighlightingRule(pattern, stringFormat)
        self.highlightingRules.append(rule)

        # singleQuotedString
        pattern = QRegularExpression("\'.*\'")
        singleQuotedStringFormat.setForeground(brush)
        rule = HighlightingRule(pattern, singleQuotedStringFormat)
        self.highlightingRules.append(rule)

    def highlightBlock(self, text):
        for rule in self.highlightingRules:
            expression = rule.pattern
            rule.pattern.setPatternOptions(QRegularExpression.InvertedGreedinessOption)
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), rule.format)


class HighlightingRule:
    def __init__(self, pattern: QRegularExpression, patternFormat: QTextCharFormat):
        self.pattern = pattern
        self.format = patternFormat
