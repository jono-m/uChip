"""A Python code editor: line numbers, syntax highlighting, auto-indent, comment toggling, bracket
matching, word completion and hover help for the scripting API."""
import html
import math
import re
from typing import Callable, List, Optional, Tuple

from PySide6.QtCore import QEvent, QRect, Qt
from PySide6.QtGui import (QColor, QFont, QFontDatabase, QGuiApplication, QPainter, QPalette, QStandardItem,
                           QStandardItemModel, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QTextFormat,
                           QTextOption)
from PySide6.QtWidgets import QCompleter, QPlainTextEdit, QTextEdit, QToolTip, QWidget

from backend.script_docs import API_NAMES, PYTHON_BUILTINS, PYTHON_KEYWORDS, api_docs, api_symbols
from gui.widgets import EventHook

INDENT = 4
BRACKETS = {"(": ")", "[": "]", "{": "}"}
DEDENT_KEYWORDS = ("return", "pass", "break", "continue", "raise")
MIN_COMPLETION_PREFIX = 2


def _utf16_length(text: str) -> int:
    """Length of [text] in Qt document positions."""
    return len(text.encode("utf-16-le")) // 2


# Tokenizing

# Block states: inside a ''' or """ string that continues onto the next line.
NORMAL, IN_SINGLE_TRIPLE, IN_DOUBLE_TRIPLE = 0, 1, 2
TRIPLE_QUOTES = {IN_SINGLE_TRIPLE: "'''", IN_DOUBLE_TRIPLE: '"""'}

CONTROL_KEYWORDS = {"if", "elif", "else", "for", "while", "break", "continue", "return", "yield", "try", "except",
                    "finally", "raise", "with", "import", "from", "as", "pass", "await", "assert", "del"}
TOKEN_RE = re.compile(r"""
    (?P<comment>\#.*)
  | (?P<string>[rRbBuUfF]{0,2}(?:'''|\"\"\"|'|"))
  | (?P<number>(?<![\w.])(?:0[xXoObB][0-9a-fA-F_]+|(?:\d[\d_]*\.?[\d_]*|\.\d[\d_]*)(?:[eE][+-]?\d+)?[jJ]?))
  | (?P<decorator>@[A-Za-z_][\w.]*)
  | (?P<name>[A-Za-z_]\w*)
""", re.VERBOSE)
API_MEMBER_NAMES = {s.name for s in api_symbols() if s.member}


def _string_end(text: str, start: int, quote: str) -> int:
    """The index just after the [quote] that closes a string from [start], or -1 if it isn't closed."""
    i = start
    while i < len(text):
        if text[i] == "\\":
            i += 2
        elif text.startswith(quote, i):
            return i + len(quote)
        else:
            i += 1
    return -1


def tokenize_line(text: str, state: int) -> Tuple[List[Tuple[int, int, str]], int]:
    """The highlighted tokens of a line, as (start, length, kind), and the state the next line starts in.

    Kinds: comment, string, open_string (not closed on this line), number, decorator, keyword,
    control, self, builtin, api, function, class, call.
    """
    tokens = []
    position = 0
    if state in TRIPLE_QUOTES:
        end = _string_end(text, 0, TRIPLE_QUOTES[state])
        if end < 0:
            return [(0, len(text), "open_string")], state
        tokens.append((0, end, "string"))
        position = end
    previous_word = ""
    while True:
        match = TOKEN_RE.search(text, position)
        if match is None:
            return tokens, NORMAL
        start, kind = match.start(), match.lastgroup
        position = match.end()
        if kind == "string":
            quote = match.group().lstrip("rRbBuUfF")
            end = _string_end(text, position, quote)
            if end < 0:
                tokens.append((start, len(text) - start, "open_string"))
                return tokens, (IN_SINGLE_TRIPLE if quote == "'''" else IN_DOUBLE_TRIPLE if quote == '"""'
                                else NORMAL)
            tokens.append((start, end - start, "string"))
            position = end
            previous_word = ""
            continue
        if kind == "name":
            word = match.group()
            after_dot = text[:start].rstrip().endswith(".")
            if previous_word == "def":
                kind = "function"
            elif previous_word == "class":
                kind = "class"
            elif after_dot:
                kind = "api" if word in API_MEMBER_NAMES else "call" if text[position:].lstrip().startswith("(") \
                    else ""
            elif word in CONTROL_KEYWORDS:
                kind = "control"
            elif word in PYTHON_KEYWORDS:
                kind = "keyword"
            elif word in ("self", "cls"):
                kind = "self"
            elif word in API_NAMES:
                kind = "api"
            elif word in PYTHON_BUILTINS:
                kind = "builtin"
            elif text[position:].lstrip().startswith("("):
                kind = "call"
            else:
                kind = ""
            previous_word = word
        else:
            previous_word = ""
        if kind:
            tokens.append((start, position - start, kind))


def _format(color: str, bold=False, italic=False) -> QTextCharFormat:
    text_format = QTextCharFormat()
    text_format.setForeground(QColor(color))
    if bold:
        text_format.setFontWeight(QFont.Weight.Bold)
    text_format.setFontItalic(italic)
    return text_format


def _token_formats() -> dict:
    """Formats per token kind, in VS Code's default dark or light colors to match the theme."""
    dark = QGuiApplication.palette().color(QPalette.Base).lightness() < 128

    def color(dark_color: str, light_color: str) -> str:
        return dark_color if dark else light_color

    string = _format(color("#ce9178", "#a31515"))
    return {
        "comment": _format(color("#6a9955", "#008000"), italic=True),
        "string": string,
        "open_string": string,
        "number": _format(color("#b5cea8", "#098658")),
        "decorator": _format(color("#dcdcaa", "#795e26")),
        "keyword": _format(color("#569cd6", "#0000ff"), bold=True),
        "control": _format(color("#c586c0", "#af00db"), bold=True),
        "self": _format(color("#9cdcfe", "#001080"), italic=True),
        "builtin": _format(color("#4ec9b0", "#267f99")),
        "api": _format(color("#4fc1ff", "#0070c1"), bold=True),
        "function": _format(color("#dcdcaa", "#795e26"), bold=True),
        "class": _format(color("#4ec9b0", "#267f99"), bold=True),
        "call": _format(color("#dcdcaa", "#795e26")),
    }


# Subclassed because Qt only allows custom highlighting through highlightBlock().
class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.formats = _token_formats()

    def highlightBlock(self, text) -> None:
        tokens, state = tokenize_line(text, max(self.previousBlockState(), NORMAL))
        for start, length, kind in tokens:
            self.setFormat(start, length, self.formats[kind])
        self.setCurrentBlockState(state)


def api_help_html(word: str) -> str:
    """Hover/completion help for an API name, or "" if [word] isn't one."""
    return "<br><br>".join("<b><code>%s</code></b><br>%s" % (html.escape(s.signature), html.escape(s.doc))
                           for s in api_docs().get(word, []))


# Subclassed because Qt only allows custom key handling and resizing through these overrides.
class PythonEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        # A line with a syntax error, underlined (0-based block number).
        self.error_line: Optional[int] = None
        self.line_numbers = QWidget(self)
        EventHook(self.line_numbers, {QEvent.Paint: lambda event: self.paint_line_numbers(event)})
        EventHook(self.viewport(), {QEvent.ToolTip: lambda event: self.show_hover_help(event)})
        self.blockCountChanged.connect(lambda: self.update_line_number_margin())
        self.cursorPositionChanged.connect(self.line_numbers.update)
        self.cursorPositionChanged.connect(lambda: self.update_extra_selections())
        self.updateRequest.connect(lambda rect, dy: self.line_numbers.scroll(0, dy))
        self.highlighter = PythonHighlighter(self.document())

        self.completion_model = QStandardItemModel(self)
        self.completion_words: List[str] = []
        self.completer = QCompleter(self.completion_model, self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.completer.setMaxVisibleItems(12)
        self.completer.activated[str].connect(self.insert_completion)

        self.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        self.setWordWrapMode(QTextOption.WrapMode.NoWrap)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * INDENT)
        self.update_line_number_margin()
        self.update_extra_selections()

    # Keys

    def keyPressEvent(self, event) -> None:
        key, modifiers = event.key(), event.modifiers()
        cursor = self.textCursor()
        if self.completer.popup().isVisible() and key in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab,
                                                          Qt.Key_Backtab, Qt.Key_Escape):
            event.ignore()  # The completer handles these.
            return
        if self.isReadOnly():
            super().keyPressEvent(event)
            return
        if key == Qt.Key_Tab:
            if cursor.hasSelection():
                self.indent_lines(1)
            else:
                cursor.insertText(" " * (INDENT - cursor.positionInBlock() % INDENT))
        elif key == Qt.Key_Backtab:
            self.indent_lines(-1)
        elif key in (Qt.Key_Return, Qt.Key_Enter) and not modifiers & Qt.ControlModifier:
            self.insert_newline()
        elif key == Qt.Key_Home and not modifiers & Qt.ControlModifier:
            self.smart_home(bool(modifiers & Qt.ShiftModifier))
        elif key == Qt.Key_Backspace and not cursor.hasSelection() and cursor.positionInBlock() > 0 and \
                cursor.block().text()[:cursor.positionInBlock()].strip(" ") == "":
            # Backspace in leading whitespace removes back to the previous indent level.
            leading = cursor.positionInBlock()
            target = math.ceil(max(0, leading - INDENT) / INDENT) * INDENT
            cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, leading - target)
            cursor.removeSelectedText()
        else:
            super().keyPressEvent(event)

        text = event.text()
        if text and (text[-1].isalnum() or text[-1] in "_."):
            self.show_completions(False)
        elif key == Qt.Key_Backspace and self.completer.popup().isVisible():
            self.show_completions(False)
        else:
            self.completer.popup().hide()

    def insert_newline(self):
        """Starts a new line at the current indent, one level deeper after a ':', or shallower after return etc."""
        cursor = self.textCursor()
        line = cursor.block().text()[:cursor.positionInBlock()]
        indent = len(line) - len(line.lstrip(" "))
        code = line.split("#")[0].rstrip()
        words = code.split()
        if code.endswith(":"):
            indent += INDENT
        elif words and words[0] in DEDENT_KEYWORDS:
            indent = max(0, indent - INDENT)
        cursor.insertText("\n" + " " * indent)
        self.ensureCursorVisible()

    def smart_home(self, select: bool):
        """Moves to the first non-space character of the line, or to the line start if already there."""
        cursor = self.textCursor()
        text = cursor.block().text()
        first = len(text) - len(text.lstrip(" "))
        column = 0 if cursor.positionInBlock() == first else first
        cursor.setPosition(cursor.block().position() + column,
                           QTextCursor.KeepAnchor if select else QTextCursor.MoveAnchor)
        self.setTextCursor(cursor)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.place_line_numbers()

    def place_line_numbers(self):
        rect = self.contentsRect()
        self.line_numbers.setGeometry(QRect(rect.left(), rect.top(), self.line_number_width(), rect.height()))

    # Editing whole lines

    def transform_lines(self, transform: Callable[[List[str]], List[str]]):
        """Replaces the lines touched by the selection (or the cursor's line) with transform(lines), as
        one undo step."""
        cursor = self.textCursor()
        document = self.document()
        had_selection = cursor.hasSelection()
        first = document.findBlock(cursor.selectionStart())
        last = document.findBlock(cursor.selectionEnd())
        # A selection ending at the start of a line doesn't include that line.
        if had_selection and last != first and cursor.selectionEnd() == last.position():
            last = last.previous()
        blocks = [first]
        while blocks[-1] != last:
            blocks.append(blocks[-1].next())
        lines = [b.text() for b in blocks]
        new_lines = transform(lines)
        if new_lines == lines:
            return
        column = cursor.positionInBlock()

        start = first.position()
        cursor.beginEditBlock()
        cursor.setPosition(start)
        cursor.setPosition(last.position() + last.length() - 1, QTextCursor.KeepAnchor)
        cursor.insertText("\n".join(new_lines))
        cursor.endEditBlock()
        if had_selection or len(lines) > 1:
            cursor.setPosition(start)
            cursor.setPosition(start + _utf16_length("\n".join(new_lines)), QTextCursor.KeepAnchor)
        else:
            column = max(0, min(column + len(new_lines[0]) - len(lines[0]), len(new_lines[0])))
            cursor.setPosition(start + _utf16_length(new_lines[0][:column]))
        self.setTextCursor(cursor)

    def indent_lines(self, direction: int):
        """Indents (direction 1) or dedents (-1) the selected lines to the next indent level."""
        def shift(line: str) -> str:
            if line.strip() == "":
                return line
            old = len(line) - len(line.lstrip(" "))
            new = (math.ceil if direction < 0 else math.floor)(max(0, old + direction * INDENT) / INDENT) * INDENT
            return " " * new + line.lstrip(" ")

        self.transform_lines(lambda lines: [shift(line) for line in lines])

    def toggle_comment(self):
        """Comments out the selected lines, or uncomments them if they are all comments."""
        def toggle(lines: List[str]) -> List[str]:
            code = [line for line in lines if line.strip()]
            if not code:
                return lines
            if all(line.lstrip().startswith("#") for line in code):
                return [re.sub(r"^(\s*)# ?", r"\1", line) for line in lines]
            column = min(len(line) - len(line.lstrip(" ")) for line in code)
            return [line[:column] + "# " + line[column:] if line.strip() else line for line in lines]

        self.transform_lines(toggle)

    def go_to_line(self, line: int):
        """Moves the cursor to the start of [line] (1-based)."""
        block = self.document().findBlockByNumber(max(0, line - 1))
        cursor = self.textCursor()
        cursor.setPosition(block.position())
        self.setTextCursor(cursor)
        self.centerCursor()
        self.setFocus()

    # Highlights: current line, matching bracket and syntax error

    def matching_bracket(self) -> Optional[Tuple[int, int]]:
        """Positions of the bracket next to the cursor and its match."""
        text = self.toPlainText()
        position = self.textCursor().position()
        closers = {v: k for k, v in BRACKETS.items()}
        for p in (position - 1, position):
            if not 0 <= p < len(text) or (text[p] not in BRACKETS and text[p] not in closers):
                continue
            opening = text[p] in BRACKETS
            open_char = text[p] if opening else closers[text[p]]
            close_char = BRACKETS[open_char]
            depth, step = 0, 1 if opening else -1
            i = p
            while 0 <= i < len(text):
                if text[i] == open_char:
                    depth += step
                elif text[i] == close_char:
                    depth -= step
                if depth == 0:
                    return p, i
                i += step
            return None
        return None

    def update_extra_selections(self):
        palette = self.palette()
        selections = []

        def add(cursor: QTextCursor, text_format: QTextCharFormat):
            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format = text_format
            selections.append(selection)

        if not self.isReadOnly():
            line_format = QTextCharFormat()
            line_format.setBackground(palette.color(QPalette.AlternateBase))
            line_format.setProperty(QTextFormat.FullWidthSelection, True)
            cursor = self.textCursor()
            cursor.clearSelection()
            add(cursor, line_format)

        if self.error_line is not None:
            block = self.document().findBlockByNumber(self.error_line)
            if block.isValid():
                error_format = QTextCharFormat()
                error_format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
                error_format.setUnderlineColor(QColor("#e51400"))
                cursor = QTextCursor(block)
                cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
                add(cursor, error_format)

        brackets = self.matching_bracket()
        if brackets is not None:
            bracket_format = QTextCharFormat()
            bracket_format.setBackground(palette.color(QPalette.Highlight).lighter(160)
                                         if palette.color(QPalette.Base).lightness() >= 128 else
                                         palette.color(QPalette.Highlight).darker(160))
            for p in brackets:
                cursor = self.textCursor()
                cursor.setPosition(p)
                cursor.setPosition(p + 1, QTextCursor.KeepAnchor)
                add(cursor, bracket_format)
        self.setExtraSelections(selections)

    def set_error_line(self, line: Optional[int]):
        if line != self.error_line:
            self.error_line = line
            self.update_extra_selections()

    # Completion and help

    def completion_prefix(self) -> Tuple[str, bool]:
        """The identifier being typed before the cursor, and whether it follows a '.'."""
        cursor = self.textCursor()
        line = cursor.block().text()[:cursor.positionInBlock()]
        match = re.search(r"[A-Za-z_]\w*$", line)
        prefix = match.group() if match else ""
        return prefix, line[:len(line) - len(prefix)].endswith(".")

    def cursor_in_code(self) -> bool:
        """Whether the cursor is outside of strings and comments."""
        cursor = self.textCursor()
        block = cursor.block()
        state = block.previous().userState() if block.previous().isValid() else NORMAL
        tokens, _ = tokenize_line(block.text(), max(state, NORMAL))
        column = cursor.positionInBlock()
        for start, length, kind in tokens:
            if kind in ("comment", "open_string") and start < column or \
                    kind == "string" and start < column < start + length:
                return False
        return True

    def _completion_candidates(self, prefix: str, member: bool) -> List[str]:
        document_words = re.findall(r"[A-Za-z_]\w+", self.toPlainText())
        words = set(document_words)
        # The word being typed isn't a suggestion unless it also appears elsewhere.
        if document_words.count(prefix) <= 1:
            words.discard(prefix)
        if member:
            words |= API_MEMBER_NAMES
        else:
            words |= set(PYTHON_KEYWORDS) | set(PYTHON_BUILTINS) | set(API_NAMES)
        return sorted(words, key=str.lower)

    def show_completions(self, force: bool):
        """Shows suggestions for the word being typed. Unless [force]d, only in code and after a
        couple of characters (or a '.')."""
        popup = self.completer.popup()
        prefix, member = self.completion_prefix()
        if not force and (self.isReadOnly() or not self.cursor_in_code() or
                          (len(prefix) < MIN_COMPLETION_PREFIX and not (member and prefix == ""))):
            popup.hide()
            return
        words = self._completion_candidates(prefix, member)
        if words != self.completion_words:
            self.completion_words = words
            self.completion_model.clear()
            for word in words:
                item = QStandardItem(word)
                help_html = api_help_html(word)
                if help_html:
                    item.setToolTip(help_html)
                self.completion_model.appendRow(item)
        self.completer.setCompletionPrefix(prefix)
        count = self.completer.completionCount()
        if count == 0 or (count == 1 and self.completer.currentCompletion() == prefix):
            popup.hide()
            return
        popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
        rect = self.cursorRect()
        rect.setWidth(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width() + 12)
        self.completer.complete(rect)

    def insert_completion(self, word: str):
        prefix, _ = self.completion_prefix()
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, _utf16_length(prefix))
        cursor.insertText(word)
        self.setTextCursor(cursor)

    def show_hover_help(self, event) -> bool:
        cursor = self.cursorForPosition(event.pos())
        cursor.select(QTextCursor.WordUnderCursor)
        help_html = api_help_html(cursor.selectedText())
        if help_html:
            QToolTip.showText(event.globalPos(), help_html, self.viewport())
        else:
            QToolTip.hideText()
        return True

    # Line numbers

    def line_number_width(self) -> int:
        digits = math.ceil(math.log10(self.blockCount() + 1))
        return 15 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_number_margin(self):
        self.setViewportMargins(self.line_number_width(), 0, 0, 0)
        self.line_numbers.update()

    def paint_line_numbers(self, event) -> bool:
        gutter = self.line_numbers
        painter = QPainter(gutter)
        palette = self.palette()
        painter.fillRect(event.rect(), palette.color(QPalette.Window))
        painter.setFont(self.font())
        block = self.firstVisibleBlock()
        number = block.blockNumber()
        geometry = self.blockBoundingGeometry(block)
        height = round(geometry.height())
        top = round(geometry.translated(self.contentOffset()).top())
        line_height = self.fontMetrics().height()
        active = self.textCursor().blockNumber()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and top + height >= event.rect().top():
                if number == active:
                    painter.fillRect(0, top, gutter.width(), line_height, palette.color(QPalette.AlternateBase))
                if number == self.error_line:
                    painter.setPen(QColor("#e51400"))
                else:
                    painter.setPen(palette.color(QPalette.Text if number == active else QPalette.PlaceholderText))
                painter.drawText(0, top, gutter.width() - 5, line_height,
                                 Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(number + 1))
            block = block.next()
            top += height
            number += 1
        painter.end()
        return True

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.FontChange:  # Zooming changes the font.
            self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * INDENT)
            self.update_line_number_margin()
            self.place_line_numbers()
