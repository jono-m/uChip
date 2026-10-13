"""The main window: the chip canvas with the inspector and rig panels docked beside it."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QAction, QIcon, QImage, QKeySequence
from PySide6.QtWidgets import (QAbstractSpinBox, QApplication, QDockWidget, QFileDialog, QLineEdit, QMainWindow,
                               QMessageBox, QPlainTextEdit, QScrollArea, QToolBar, QWidget)

from backend import project_file
from backend.chip import Script
from backend.runner import Runner
from backend.session import Session
from gui.canvas import GRID_SPACING, Canvas, build_canvas
from gui.inspector import Inspector, build_inspector, refresh_inspector
from gui.rig_panel import RigPanel, build_rig_panel
from gui.script_browser import ScriptBrowser, build_script_browser
from gui.script_editor import ScriptEditor, build_script_editor
from gui.widgets import APP_ICON_FILE, EventHook, browse_for_image, theme_icon

STUCK_TIMEOUT = 5.0
TEXT_INPUTS = (QLineEdit, QAbstractSpinBox, QPlainTextEdit)


def _focused_text_input(window: QMainWindow) -> Optional[QWidget]:
    focus = QApplication.focusWidget()
    return focus if isinstance(focus, TEXT_INPUTS) and focus.window() is window else None


def _is_mid_edit(window: QMainWindow) -> bool:
    """Whether the user is partway through an edit: dragging, or typing in a field of [window]. Undo
    steps are only recorded between edits, so a drag or a typed name becomes one step."""
    return QApplication.mouseButtons() != Qt.NoButton or _focused_text_input(window) is not None


@dataclass(eq=False)
class MainWindow:
    window: QMainWindow
    session: Session
    runner: Runner
    canvas: Canvas
    inspector: Inspector
    rig_panel: RigPanel
    script_browser: ScriptBrowser
    inspector_dock: QDockWidget
    rig_dock: QDockWidget
    edit_action: QAction
    editing_actions: List[QAction]
    undo_action: QAction
    redo_action: QAction
    script_editors: List[ScriptEditor] = field(default_factory=list)

    def refresh(self):
        self.canvas.refresh()
        refresh_inspector(self.inspector, self.canvas)
        self.rig_panel.refresh()
        # Only edit mode changes are undoable; changes made while running are kept as they are.
        if not self.canvas.editing:
            self.session.accept_changes()
        elif not _is_mid_edit(self.window):
            self.session.record_edit()
        history = self.session.history
        self.undo_action.setEnabled(self.canvas.editing and bool(history.undo_steps))
        self.redo_action.setEnabled(self.canvas.editing and bool(history.redo_steps))
        title = "µChip - %s%s" % (self.session.chip_name(), "*" if self.session.is_modified() else "")
        if self.window.windowTitle() != title:
            self.window.setWindowTitle(title)

    def check_stuck(self):
        stuck = self.runner.stuck_function(STUCK_TIMEOUT)
        if stuck is not None:
            QMessageBox.critical(self.window, "Stuck",
                                 "Function %s in program %s has blocked the update thread for >%d seconds. Ensure "
                                 "that this script does not have a long-running or infinite loop. Programs may not "
                                 "run until uChip is restarted." % (stuck[1], stuck[0], STUCK_TIMEOUT))

    # Editing

    def set_editing(self, editing: bool):
        if not editing:
            self.session.record_edit()
        self.canvas.set_editing(editing)
        self.edit_action.setChecked(editing)
        self.edit_action.setText("Finish" if editing else "Edit")
        self.edit_action.setIcon(theme_icon("assets/icons/check.png" if editing else "assets/icons/edit.png"))
        for a in self.editing_actions:
            a.setEnabled(editing)
        (self.inspector_dock if editing else self.rig_dock).raise_()

    def add_element(self, element):
        self.canvas.place_at_center(element)

    def add_image_element(self):
        path = browse_for_image(self.window)
        if path is not None:
            size = QImage(str(path)).size()
            self.add_element(self.session.chip.add_image(path, (size.width(), size.height())))

    def duplicate_selection(self):
        copies = self.session.chip.duplicate_elements(self.canvas.selection, (GRID_SPACING, GRID_SPACING))
        self.canvas.refresh()
        self.canvas.select(copies)

    def delete_selection(self):
        self.session.chip.remove_elements(self.canvas.selection)
        self.canvas.refresh()

    def undo(self, redo: bool = False):
        # Finish any edit in a focused field first, so it is undone too and the field shows the result.
        field_widget = _focused_text_input(self.window)
        if field_widget is not None:
            field_widget.clearFocus()
        if redo:
            self.session.redo()
        else:
            self.session.undo()
        self.refresh()

    def open_editor(self, script: Optional[Script]):
        """Opens a script editor, or brings an existing one for [script] to the front."""
        self.script_editors = [e for e in self.script_editors if e.window.isVisible()]
        existing = next((e for e in self.script_editors if script is not None and e.script == script), None)
        if existing is not None:
            existing.window.activateWindow()
            existing.window.raise_()
            return
        self.script_editors.append(build_script_editor(self.session, script, self.script_browser.relist))

    # Files

    def prompt_save_changes(self) -> bool:
        """Offers to save unsaved changes. Returns False if the user cancels."""
        if not self.session.is_modified():
            return True
        answer = QMessageBox.critical(self.window, "Confirm Action",
                                      "This uChip project has been modified. Do you want to discard changes?",
                                      QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard |
                                      QMessageBox.StandardButton.Cancel)
        if answer == QMessageBox.StandardButton.Cancel:
            return False
        if answer == QMessageBox.StandardButton.Save:
            return self.save_chip(False)
        return True

    def new_chip(self):
        if self.prompt_save_changes():
            self.session.new_chip()
            self.canvas.refresh()

    def open_chip_dialog(self):
        if not self.prompt_save_changes():
            return
        path, _ = QFileDialog.getOpenFileName(self.window, "Open Chip", filter=project_file.FILE_FILTER)
        if path:
            self.open_chip(Path(path))

    def open_chip(self, path: Path):
        try:
            self.session.open_chip(path)
        except (OSError, ValueError, KeyError) as e:
            QMessageBox.critical(self.window, "Could not open chip", str(e))
            return
        self.canvas.refresh()
        self.canvas.zoom_to_fit()

    def save_chip(self, save_as: bool) -> bool:
        path = self.session.path
        if save_as or path is None:
            chosen, _ = QFileDialog.getSaveFileName(self.window, "Save Path", filter=project_file.FILE_FILTER)
            if not chosen:
                return False
            path = Path(chosen).with_suffix(project_file.FILE_EXTENSION)
        try:
            self.session.save_chip(path)
        except OSError as e:
            QMessageBox.critical(self.window, "Could not save chip", str(e))
            return False
        return True


def build_main_window(session: Session, runner: Runner, on_devices_changed=lambda: None) -> MainWindow:
    window = QMainWindow()
    window.setWindowIcon(QIcon(APP_ICON_FILE))
    window.resize(1600, 900)

    canvas = build_canvas(session, runner)
    window.setCentralWidget(canvas.view)

    # The script browser and inspector need to open other windows; they are given functions to do
    # so, which are filled in once the main window record exists.
    main: Optional[MainWindow] = None

    def open_script_editor(script: Optional[Script]):
        main.open_editor(script)

    def choose_script(on_chosen, selected):
        main.script_browser.show(on_chosen, selected)

    inspector = build_inspector(session, runner, choose_script, open_script_editor)
    rig_panel = build_rig_panel(session.rig, on_devices_changed)
    script_browser = build_script_browser(session, window, open_script_editor)

    def dock(title: str, widget) -> QDockWidget:
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        d = QDockWidget(title, window)
        d.setObjectName(title)
        d.setWidget(scroll)
        d.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)
        window.addDockWidget(Qt.RightDockWidgetArea, d)
        return d

    inspector_dock = dock("Inspector", inspector.widget)
    rig_dock = dock("Rig", rig_panel.widget)
    window.tabifyDockWidget(inspector_dock, rig_dock)

    def action(text: str, slot, shortcut: str = None, icon: str = None) -> QAction:
        a = QAction(text, window)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        if icon:
            a.setIcon(theme_icon(icon))
        a.triggered.connect(lambda checked=False: slot())
        return a

    edit_action = action("Edit Chip", lambda: main.set_editing(main.edit_action.isChecked()), "Ctrl+E",
                         "assets/icons/edit.png")
    edit_action.setCheckable(True)
    add_valve = action("Valve", lambda: main.add_element(session.chip.add_valve()), icon="assets/icons/valve.png")
    add_image = action("Image", lambda: main.add_image_element(), icon="assets/icons/image.png")
    add_text = action("Text", lambda: main.add_element(session.chip.add_text()), icon="assets/icons/text.png")
    add_program = action("Program", lambda: choose_script(lambda s: main.add_element(session.chip.add_program(s)),
                                                          None), icon="assets/icons/code.png")
    undo = action("Undo", lambda: main.undo(), "Ctrl+Z")
    redo = action("Redo", lambda: main.undo(redo=True))
    redo.setShortcuts([QKeySequence("Ctrl+Y"), QKeySequence("Ctrl+Shift+Z")])
    duplicate = action("Duplicate", lambda: main.duplicate_selection(), "Ctrl+D")
    delete = action("Delete", lambda: main.delete_selection(), "Delete")
    select_all = action("Select All", lambda: canvas.select(list(canvas.elements)), "Ctrl+A")
    select_none = action("Select None", lambda: canvas.select([]), "Esc")

    menu = window.menuBar()
    file_menu = menu.addMenu("&File")
    file_menu.addAction(action("New", lambda: main.new_chip(), "Ctrl+N"))
    file_menu.addAction(action("Open...", lambda: main.open_chip_dialog(), "Ctrl+O"))
    file_menu.addAction(action("Save", lambda: main.save_chip(False), "Ctrl+S"))
    file_menu.addAction(action("Save As...", lambda: main.save_chip(True), "Ctrl+Shift+S"))
    file_menu.addSeparator()
    file_menu.addAction(action("Exit", window.close))
    edit_menu = menu.addMenu("&Edit")
    edit_menu.addAction(edit_action)
    edit_menu.addSeparator()
    edit_menu.addActions([undo, redo])
    edit_menu.addSeparator()
    add_menu = edit_menu.addMenu("Add")
    add_menu.addActions([add_valve, add_image, add_text, add_program])
    edit_menu.addActions([duplicate, delete])
    edit_menu.addSeparator()
    edit_menu.addActions([select_all, select_none])
    view_menu = menu.addMenu("&View")
    view_menu.addAction(action("Zoom to Fit", canvas.zoom_to_fit, "Ctrl+0"))
    view_menu.addAction(action("Center on Selection", canvas.center_on_selection))
    view_menu.addSeparator()
    view_menu.addActions([inspector_dock.toggleViewAction(), rig_dock.toggleViewAction()])

    toolbar = QToolBar("Tools")
    toolbar.setObjectName("Tools")
    toolbar.setMovable(False)
    toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
    toolbar.addAction(edit_action)
    toolbar.addSeparator()
    toolbar.addActions([add_valve, add_image, add_text, add_program])
    window.addToolBar(Qt.LeftToolBarArea, toolbar)

    main = MainWindow(window, session, runner, canvas, inspector, rig_panel, script_browser, inspector_dock, rig_dock,
                      edit_action, [add_valve, add_image, add_text, add_program, duplicate, delete, select_all,
                                    select_none], undo, redo)

    # Set once the user confirms closing, so a repeated close event can't prompt to save again.
    closing = False

    def on_close(event):
        nonlocal closing
        if closing:
            return False
        if not main.prompt_save_changes():
            event.ignore()
            return True
        closing = True
        for editor in main.script_editors:
            if editor.window.isVisible():
                editor.window.close()
        return False

    EventHook(window, {QEvent.Close: on_close})
    main.set_editing(True)
    return main
