"""A window for editing a script file, with a find/replace bar, live syntax checking and the scripting
reference alongside."""
import html
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QPalette, QTextCursor, QTextDocument
from PySide6.QtWidgets import (QCheckBox, QFileDialog, QGridLayout, QInputDialog, QLabel, QLineEdit, QMainWindow,
                               QMessageBox, QPushButton, QSplitter, QTextBrowser, QToolButton, QVBoxLayout, QWidget)

from backend.chip import Script, write_script
from backend.script_docs import api_symbols
from backend.session import Session
from gui.python_editor import PythonEditor
from gui.script_browser import SCRIPT_FILTER
from gui.widgets import APP_ICON_FILE, EventHook

REFERENCE_FILE = Path("assets/docs/scripting_reference.html")
SYNTAX_CHECK_DELAY_MS = 400


def reference_html() -> str:
    """The scripting reference, with its full API section generated from the API's docstrings."""
    rows = []
    for symbol in api_symbols():
        rows.append("<p style='margin-left: %dpx'><code><b>%s</b></code><br>%s</p>" % (
            20 if symbol.member else 0, html.escape(symbol.signature), html.escape(symbol.doc).replace("\n", "<br>")))
    return REFERENCE_FILE.read_text().replace("<!-- API -->", "\n".join(rows))


@dataclass(eq=False)
class FindBar:
    widget: QWidget
    find: QLineEdit
    replace: QLineEdit
    match_case: QCheckBox
    status: QLabel


@dataclass(eq=False)
class ScriptEditor:
    window: QMainWindow
    editor: PythonEditor
    find_bar: FindBar
    position_label: QLabel
    syntax_label: QLabel
    session: Session
    script: Optional[Script]
    on_saved: Callable[[Script], None]

    def update_title(self):
        name = str(self.script.path) if self.script is not None else "New script"
        modified = "*" if self.editor.document().isModified() else ""
        self.window.setWindowTitle(name + modified + " - uChip Editor")

    def save(self, save_as: bool = False) -> bool:
        path = self.script.path if self.script is not None else None
        if save_as or path is None:
            chosen, _ = QFileDialog.getSaveFileName(self.window, "Save Script", filter=SCRIPT_FILTER)
            if not chosen:
                return False
            path = Path(chosen).with_suffix(".py")
        try:
            write_script(path, self.editor.toPlainText())
        except OSError as e:
            QMessageBox.critical(self.window, "Could not save script", str(e))
            return False
        if self.script is None or path != self.script.path:
            self.script = self.session.chip.import_script(path)
        self.editor.document().setModified(False)
        self.update_title()
        self.on_saved(self.script)
        return True

    def prompt_close(self) -> bool:
        """Asks to save unsaved changes. Returns False if the user cancels."""
        if not self.editor.document().isModified():
            return True
        answer = QMessageBox.critical(self.window, "Confirm Action",
                                      "This script has been modified. Do you want to discard changes?",
                                      QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard |
                                      QMessageBox.StandardButton.Cancel)
        if answer == QMessageBox.StandardButton.Cancel:
            return False
        if answer == QMessageBox.StandardButton.Save:
            return self.save()
        return True

    # Status

    def update_position(self):
        cursor = self.editor.textCursor()
        self.position_label.setText("Ln %d, Col %d" % (cursor.blockNumber() + 1, cursor.positionInBlock() + 1))

    def check_syntax(self):
        """Shows the first syntax error (if any) in the status bar and underlines its line."""
        try:
            compile(self.editor.toPlainText(), "script", "exec")
        except SyntaxError as e:
            line = e.lineno or 1
            self.syntax_label.setText("<span style='color: #e51400'>Line %d: %s</span>" % (line, html.escape(e.msg)))
            self.editor.set_error_line(line - 1)
            return
        except ValueError as e:  # e.g. null bytes
            self.syntax_label.setText(html.escape(str(e)))
            return
        self.syntax_label.setText("No syntax errors")
        self.editor.set_error_line(None)

    # Find and replace

    def show_find(self, replace: bool):
        selected = self.editor.textCursor().selectedText()
        if selected and " " not in selected:
            self.find_bar.find.setText(selected)
        self.find_bar.widget.show()
        field = self.find_bar.replace if replace and self.find_bar.find.text() else self.find_bar.find
        field.setFocus()
        field.selectAll()

    def hide_find(self):
        self.find_bar.widget.hide()
        self.editor.setFocus()

    def _find_flags(self, backward: bool) -> QTextDocument.FindFlag:
        flags = QTextDocument.FindFlag(0)
        if backward:
            flags |= QTextDocument.FindBackward
        if self.find_bar.match_case.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        return flags

    def find_next(self, backward: bool = False) -> bool:
        """Selects the next match, wrapping around the end of the script."""
        text = self.find_bar.find.text()
        if not text:
            return False
        flags = self._find_flags(backward)
        found = self.editor.find(text, flags)
        if not found:
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.End if backward else QTextCursor.Start)
            self.editor.setTextCursor(cursor)
            found = self.editor.find(text, flags)
        self.find_bar.status.setText("" if found else "Not found")
        return found

    def _selection_matches(self) -> bool:
        selected = self.editor.textCursor().selectedText()
        text = self.find_bar.find.text()
        return selected == text if self.find_bar.match_case.isChecked() else selected.lower() == text.lower()

    def replace_next(self):
        if self.find_bar.find.text() and self._selection_matches():
            self.editor.textCursor().insertText(self.find_bar.replace.text())
        self.find_next()

    def replace_all(self):
        text = self.find_bar.find.text()
        if not text:
            return
        # One edit block, so Replace All is undone in one step.
        edit = self.editor.textCursor()
        edit.beginEditBlock()
        cursor = QTextCursor(self.editor.document())
        count = 0
        while True:
            cursor = self.editor.document().find(text, cursor, self._find_flags(False))
            if cursor.isNull():
                break
            cursor.insertText(self.find_bar.replace.text())
            count += 1
        edit.endEditBlock()
        self.find_bar.status.setText("Replaced %d" % count)

    def go_to_line(self):
        line, ok = QInputDialog.getInt(self.window, "Go to Line", "Line:", self.editor.textCursor().blockNumber() + 1,
                                       1, self.editor.blockCount())
        if ok:
            self.editor.go_to_line(line)


def build_find_bar() -> FindBar:
    widget = QWidget()
    find, replace = QLineEdit(), QLineEdit()
    find.setPlaceholderText("Find")
    replace.setPlaceholderText("Replace with")
    find_bar = FindBar(widget, find, replace, QCheckBox("Match case"), QLabel())
    layout = QGridLayout(widget)
    layout.setContentsMargins(6, 4, 6, 4)
    layout.addWidget(find, 0, 0)
    layout.addWidget(replace, 1, 0)
    layout.addWidget(find_bar.match_case, 0, 3)
    layout.addWidget(find_bar.status, 1, 3, 1, 2)
    layout.setColumnStretch(0, 1)
    widget.hide()
    return find_bar


def build_script_editor(session: Session, script: Optional[Script],
                        on_saved: Callable[[Script], None]) -> ScriptEditor:
    """Opens an editor for [script], or for a new script if None. [on_saved] is called after saving."""
    window = QMainWindow()
    window.setWindowIcon(QIcon(APP_ICON_FILE))
    window.resize(1400, 850)
    editor = PythonEditor()
    editor.setMinimumWidth(500)
    find_bar = build_find_bar()

    reference = QTextBrowser()
    reference.setOpenExternalLinks(True)
    reference.document().setDocumentMargin(16)
    # Code blocks get a background slightly toward the text color, which works on light and dark themes.
    base, text = reference.palette().color(QPalette.Base), reference.palette().color(QPalette.Text)
    code_background = QColor(*(round(0.92 * b + 0.08 * t) for b, t in zip(base.getRgb()[:3], text.getRgb()[:3])))
    reference.document().setDefaultStyleSheet("pre { background-color: %s; }" % code_background.name())
    reference.setHtml(reference_html())
    reference.setMinimumWidth(300)

    editor_area = QWidget()
    editor_layout = QVBoxLayout(editor_area)
    editor_layout.setContentsMargins(0, 0, 0, 0)
    editor_layout.setSpacing(0)
    editor_layout.addWidget(editor, stretch=1)
    editor_layout.addWidget(find_bar.widget)
    splitter = QSplitter()
    splitter.addWidget(editor_area)
    splitter.addWidget(reference)
    splitter.setStretchFactor(0, 1)
    splitter.setSizes([950, 450])
    window.setCentralWidget(splitter)

    position_label, syntax_label = QLabel(), QLabel()
    window.statusBar().addWidget(syntax_label, 1)
    window.statusBar().addPermanentWidget(position_label)

    script_editor = ScriptEditor(window, editor, find_bar, position_label, syntax_label, session, script, on_saved)

    def action(menu, text: str, slot, shortcuts=(), enabled_signal=None) -> QAction:
        a = menu.addAction(text)
        a.setShortcuts([QKeySequence(s) for s in shortcuts])
        a.triggered.connect(lambda checked=False: slot())
        if enabled_signal is not None:
            a.setEnabled(False)
            enabled_signal.connect(a.setEnabled)
        return a

    menu = window.menuBar()
    file_menu = menu.addMenu("&File")
    action(file_menu, "Save", lambda: script_editor.save(), ["Ctrl+S"])
    action(file_menu, "Save As...", lambda: script_editor.save(True), ["Ctrl+Shift+S"])
    file_menu.addSeparator()
    action(file_menu, "Close", window.close, ["Ctrl+W"])

    edit_menu = menu.addMenu("&Edit")
    action(edit_menu, "Undo", editor.undo, [QKeySequence.Undo], editor.undoAvailable)
    action(edit_menu, "Redo", editor.redo, ["Ctrl+Y", "Ctrl+Shift+Z"], editor.redoAvailable)
    edit_menu.addSeparator()
    action(edit_menu, "Cut", editor.cut, [QKeySequence.Cut], editor.copyAvailable)
    action(edit_menu, "Copy", editor.copy, [QKeySequence.Copy], editor.copyAvailable)
    action(edit_menu, "Paste", editor.paste, [QKeySequence.Paste])
    action(edit_menu, "Select All", editor.selectAll, [QKeySequence.SelectAll])
    edit_menu.addSeparator()
    action(edit_menu, "Indent", lambda: editor.indent_lines(1), ["Ctrl+]"])
    action(edit_menu, "Unindent", lambda: editor.indent_lines(-1), ["Ctrl+["])
    action(edit_menu, "Toggle Comment", editor.toggle_comment, ["Ctrl+/"])
    action(edit_menu, "Show Suggestions", lambda: editor.show_completions(True), ["Ctrl+Space"])
    edit_menu.addSeparator()
    action(edit_menu, "Find...", lambda: script_editor.show_find(False), [QKeySequence.Find])
    action(edit_menu, "Find Next", lambda: script_editor.find_next(), ["F3"])
    action(edit_menu, "Find Previous", lambda: script_editor.find_next(True), ["Shift+F3"])
    action(edit_menu, "Replace...", lambda: script_editor.show_find(True), ["Ctrl+H"])
    action(edit_menu, "Go to Line...", script_editor.go_to_line, ["Ctrl+G"])

    view_menu = menu.addMenu("&View")
    action(view_menu, "Zoom In", lambda: editor.zoomIn(1), ["Ctrl+=", "Ctrl++"])
    action(view_menu, "Zoom Out", lambda: editor.zoomOut(1), ["Ctrl+-"])
    default_size = editor.font().pointSizeF()

    def reset_zoom():
        font = editor.font()
        font.setPointSizeF(default_size)
        editor.setFont(font)

    action(view_menu, "Reset Zoom", reset_zoom, ["Ctrl+0"])
    view_menu.addSeparator()
    show_reference = action(view_menu, "Scripting Reference", lambda: reference.setVisible(show_reference.isChecked()),
                            ["F1"])
    show_reference.setCheckable(True)
    show_reference.setChecked(True)

    # Find bar buttons and keys.
    bar_layout: QGridLayout = find_bar.widget.layout()
    for column, (text, slot) in enumerate([("Previous", lambda: script_editor.find_next(True)),
                                           ("Next", lambda: script_editor.find_next())], start=1):
        button = QPushButton(text)
        button.clicked.connect(slot)
        bar_layout.addWidget(button, 0, column)
    for column, (text, slot) in enumerate([("Replace", script_editor.replace_next),
                                           ("Replace All", script_editor.replace_all)], start=1):
        button = QPushButton(text)
        button.clicked.connect(slot)
        bar_layout.addWidget(button, 1, column)
    close_find = QToolButton()
    close_find.setText("✕")
    close_find.setAutoRaise(True)
    close_find.setToolTip("Close (Esc)")
    close_find.clicked.connect(script_editor.hide_find)
    bar_layout.addWidget(close_find, 0, 4)

    def on_find_key(field_is_replace: bool):
        def handle(event) -> bool:
            if event.key() == Qt.Key_Escape:
                script_editor.hide_find()
                return True
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if field_is_replace:
                    script_editor.replace_next()
                else:
                    script_editor.find_next(bool(event.modifiers() & Qt.ShiftModifier))
                return True
            return False
        return handle

    EventHook(find_bar.find, {QEvent.KeyPress: on_find_key(False)})
    EventHook(find_bar.replace, {QEvent.KeyPress: on_find_key(True)})
    find_bar.find.textChanged.connect(lambda text: find_bar.status.setText(""))

    # Status bar and syntax checking, a moment after typing stops.
    syntax_timer = QTimer(window)
    syntax_timer.setSingleShot(True)
    syntax_timer.setInterval(SYNTAX_CHECK_DELAY_MS)
    syntax_timer.timeout.connect(script_editor.check_syntax)
    editor.textChanged.connect(syntax_timer.start)
    editor.cursorPositionChanged.connect(script_editor.update_position)
    editor.modificationChanged.connect(lambda modified: script_editor.update_title())

    def on_close(event):
        if not script_editor.prompt_close():
            event.ignore()
            return True
        return False

    EventHook(window, {QEvent.Close: on_close})

    if script is not None:
        editor.setPlainText(script.read())
    script_editor.update_title()
    script_editor.update_position()
    script_editor.check_syntax()
    window.show()
    window.raise_()
    editor.setFocus()
    return script_editor
