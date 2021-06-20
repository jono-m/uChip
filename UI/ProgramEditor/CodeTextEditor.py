from PySide6.QtWidgets import QFrame, QTextEdit, QHBoxLayout
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, Qt, QBrush, QKeyEvent
from PySide6.QtCore import Signal, QRegularExpression, Qt
import keyword
import re


class CodeTextEditor(QFrame):
    codeChanged = Signal()

    def __init__(self):
        super().__init__()

        self.textEdit = CodeTextEditorWidget()
        self.textEdit.setTabStopDistance(20)
        self.textEdit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.textEdit.textChanged.connect(self.codeChanged.emit)

        self.textEdit.setAcceptRichText(False)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
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


class CodeTextEditorWidget(QTextEdit):
    def keyPressEvent(self, e: QKeyEvent) -> None:
        print(e.key())
        if e.key() == Qt.Key.Key_Backtab:
            self.HandleTab(False)
        elif e.key() == Qt.Key.Key_Tab:
            self.HandleTab(True)
        else:
            super().keyPressEvent(e)

    def HandleTab(self, indent):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            if indent:
                currentPosition = cursor.position()
                cursor.movePosition(cursor.StartOfLine)
                cursor.setPosition(currentPosition, cursor.KeepAnchor)
                text = cursor.selectedText()
                cursor.setPosition(currentPosition)
                if text.strip() != '':
                    cursor.insertText("    ")
                    return

        beginning = min(cursor.anchor(), cursor.position())
        end = max(cursor.anchor(), cursor.position())

        cursor.setPosition(beginning)
        cursor.movePosition(cursor.StartOfLine)
        cursor.setPosition(end, cursor.KeepAnchor)
        cursor.movePosition(cursor.EndOfLine, cursor.KeepAnchor)

        selectedText = cursor.selectedText()
        originalLines = selectedText.split("\u2029")
        lines = originalLines.copy()
        print("L: " + str(lines))
        for lineNo in range(len(lines)):
            if indent:
                count = len(re.match("\A *", lines[lineNo])[0])
                toAdd = 4 - (count % 4)
                lines[lineNo] = " " * toAdd + lines[lineNo]
            else:
                lines[lineNo] = re.sub("\A {1,4}", "", lines[lineNo])
        newText = "\u2029".join(lines)

        cursor.removeSelectedText()
        cursor.insertText(newText)

        deltaFirstLine = len(lines[0]) - len(originalLines[0])
        cursor.setPosition(beginning + deltaFirstLine)

        deltaLastLine = sum([len(lines[i]) - len(originalLines[i]) for i in range(len(originalLines))])
        cursor.setPosition(end + deltaLastLine, cursor.KeepAnchor)

        self.setTextCursor(cursor)
