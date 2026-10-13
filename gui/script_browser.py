"""The script browser: lists the built-in and project scripts so one can be chosen for a program."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import (QDialog, QFileDialog, QHBoxLayout, QLabel, QListWidget, QMessageBox, QPushButton,
                               QVBoxLayout, QWidget)

from backend.chip import Script
from backend.session import Session
from gui.python_editor import PythonEditor
from gui.widgets import EventHook

SCRIPT_FILTER = "uChip script (*.py)"


@dataclass(eq=False)
class ScriptBrowser:
    dialog: QDialog
    session: Session
    script_list: QListWidget
    path_label: QLabel
    preview: PythonEditor
    edit_button: QPushButton
    relocate_button: QPushButton
    remove_button: QPushButton
    scripts: List[Script] = field(default_factory=list)
    on_chosen: Callable[[Script], None] = lambda script: None

    def selected_script(self) -> Optional[Script]:
        row = self.script_list.currentRow()
        return self.scripts[row] if 0 <= row < len(self.scripts) else None

    def relist(self, select: Optional[Script] = None):
        """Refreshes the list of scripts, selecting [select] (or keeping the current selection)."""
        select = select if select is not None else self.selected_script()
        self.scripts = self.session.chip.available_scripts()
        self.script_list.blockSignals(True)
        self.script_list.clear()
        self.script_list.addItems([("[built-in]  " if s.is_builtin() else "") + s.name()
                                   for s in self.scripts])
        self.script_list.setCurrentRow(self.scripts.index(select) if select in self.scripts else 0)
        self.script_list.blockSignals(False)
        self.show_selected()

    def show_selected(self):
        script = self.selected_script()
        builtin = script is not None and script.is_builtin()
        exists = script is not None and script.file().exists()
        if script is None:
            text = ""
        elif builtin:
            text = script.name() + " <i>[built-in]</i>"
        elif exists:
            text = str(script.path)
        else:
            text = "Cannot find " + str(script.path)
        self.path_label.setText(text)
        self.preview.setPlainText(script.read() if exists else "")
        self.edit_button.setEnabled(exists and not builtin)
        self.relocate_button.setVisible(script is not None and not builtin and not exists)
        in_use = script is not None and self.session.chip.script_in_use(script)
        self.remove_button.setEnabled(script is not None and not builtin and not in_use)
        self.remove_button.setToolTip("Cannot remove a built-in script." if builtin else
                                      "Cannot remove a script in use by the current project." if in_use else "")

    def show(self, on_chosen: Callable[[Script], None], selected: Optional[Script] = None):
        self.on_chosen = on_chosen
        self.relist(selected)
        self.dialog.show()
        self.dialog.raise_()


def build_script_browser(session: Session, parent: QWidget,
                         open_editor: Callable[[Optional[Script]], None]) -> ScriptBrowser:
    """[open_editor] opens a script editor for a script (or for a new script when given None)."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Script Browser")
    dialog.setModal(False)

    script_list = QListWidget()
    path_label = QLabel()
    preview = PythonEditor()
    preview.setMinimumWidth(500)
    preview.setReadOnly(True)
    edit_button = QPushButton("Edit Script...")
    relocate_button = QPushButton("Relocate...")
    choose_button = QPushButton("Choose")
    choose_button.setDefault(True)
    new_button = QPushButton("New Script...")
    import_button = QPushButton("Import...")
    remove_button = QPushButton("Remove")

    top = QHBoxLayout()
    top.addWidget(path_label, stretch=1)
    top.addWidget(relocate_button)
    top.addWidget(edit_button)
    preview_layout = QVBoxLayout()
    preview_layout.addLayout(top)
    preview_layout.addWidget(preview)
    list_layout = QVBoxLayout()
    for w in [script_list, choose_button, new_button, import_button, remove_button]:
        list_layout.addWidget(w)
    layout = QHBoxLayout(dialog)
    layout.addLayout(list_layout, stretch=0)
    layout.addLayout(preview_layout, stretch=1)

    browser = ScriptBrowser(dialog, session, script_list, path_label, preview, edit_button, relocate_button,
                            remove_button)

    def choose():
        script = browser.selected_script()
        if script is not None:
            browser.on_chosen(script)
            dialog.hide()

    def browse_for_script() -> Optional[Path]:
        path, _ = QFileDialog.getOpenFileName(dialog, "Browse for script", filter=SCRIPT_FILTER)
        return Path(path) if path else None

    def import_script():
        path = browse_for_script()
        if path is not None:
            browser.relist(session.chip.import_script(path))

    def relocate():
        path = browse_for_script()
        if path is None:
            return
        try:
            browser.relist(session.chip.relocate_script(browser.selected_script(), path))
        except ValueError as e:
            QMessageBox.critical(dialog, "Could not relocate script", str(e))

    def remove():
        try:
            session.chip.remove_script(browser.selected_script())
        except ValueError as e:
            QMessageBox.critical(dialog, "Could not remove script", str(e))
        browser.relist()

    script_list.currentRowChanged.connect(lambda row: browser.show_selected())
    script_list.itemDoubleClicked.connect(lambda item: choose())
    choose_button.clicked.connect(choose)
    new_button.clicked.connect(lambda: open_editor(None))
    edit_button.clicked.connect(lambda: open_editor(browser.selected_script()))
    import_button.clicked.connect(import_script)
    relocate_button.clicked.connect(relocate)
    remove_button.clicked.connect(remove)

    def on_key(event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            choose()
            return True
        return False

    EventHook(dialog, {QEvent.KeyPress: on_key})
    return browser


