"""The inspector panel: edits the properties of the single selected element.

The panel's contents are rebuilt when the selection changes and refreshed from the element's data on
every refresh. Edits write straight to the element's data.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from PySide6.QtGui import QColor, QIcon, QPalette, QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QColorDialog, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
                               QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget)

from backend.chip import Element, Image, Program, Script, Text, Valve
from backend.runner import Runner
from backend.session import Session
from gui.canvas import Canvas
from gui.parameter_editors import ParameterTable, build_parameter_table, refresh_parameter_table
from gui.widgets import (browse_for_image, clear_layout, sync_checked, sync_label, sync_line_edit, sync_plain_text,
                         sync_spin, theme_icon)

# Opens the script browser: (on_chosen, initially selected script).
ChooseScript = Callable[[Callable[[Script], None], Optional[Script]], None]


@dataclass(eq=False)
class Inspector:
    widget: QWidget
    layout: QVBoxLayout
    session: Session
    runner: Runner
    choose_script: ChooseScript
    edit_script: Callable[[Script], None]
    element: Optional[Element] = None
    parts: Any = None
    message: str = ""

    def show_message(self, message: str):
        clear_layout(self.layout)
        self.message = message
        label = QLabel(message)
        label.setWordWrap(True)
        self.layout.addWidget(label)
        self.layout.addStretch(1)

    def add_form(self) -> QFormLayout:
        form = QFormLayout()
        self.layout.addLayout(form)
        return form


def build_inspector(session: Session, runner: Runner, choose_script: ChooseScript,
                    edit_script: Callable[[Script], None]) -> Inspector:
    """[edit_script] opens a script in the script editor."""
    widget = QWidget()
    widget.setMinimumWidth(280)
    layout = QVBoxLayout(widget)
    inspector = Inspector(widget, layout, session, runner, choose_script, edit_script)
    inspector.show_message("Select an element to edit it.")
    return inspector


def refresh_inspector(inspector: Inspector, canvas: Canvas):
    selection = canvas.selection if canvas.editing else []
    target = selection[0] if len(selection) == 1 else None
    if target is not inspector.element:
        inspector.element = target
        if target is not None:
            clear_layout(inspector.layout)
            build, _ = INSPECTORS[type(target)]
            inspector.parts = build(target, inspector)
            inspector.layout.addStretch(1)
    if target is None:
        if not canvas.editing:
            message = "Switch to edit mode to change the chip."
        elif selection:
            message = "%d elements selected." % len(selection)
        else:
            message = "Select an element to edit it."
        if message != inspector.message:
            inspector.show_message(message)
        return
    _, refresh = INSPECTORS[type(target)]
    refresh(target, inspector.parts, inspector)


# Valves

@dataclass(eq=False)
class ValveFields:
    name: QLineEdit
    solenoid: QSpinBox


def build_valve_inspector(valve: Valve, inspector: Inspector) -> ValveFields:
    form = inspector.add_form()
    fields = ValveFields(QLineEdit(), QSpinBox())
    fields.solenoid.setRange(0, 1000)
    fields.name.textEdited.connect(lambda text: setattr(valve, "name", text))
    fields.solenoid.valueChanged.connect(lambda value: setattr(valve, "solenoid", value))
    form.addRow("Name", fields.name)
    form.addRow("Solenoid", fields.solenoid)
    return fields


def refresh_valve_inspector(valve: Valve, fields: ValveFields, inspector: Inspector):
    sync_line_edit(fields.name, valve.name)
    sync_spin(fields.solenoid, valve.solenoid)


# Text

@dataclass(eq=False)
class TextFields:
    text: QPlainTextEdit
    color: QPushButton
    default_color: QPushButton
    font_size: QSpinBox
    shown_color: object = None


def build_text_inspector(text: Text, inspector: Inspector) -> TextFields:
    fields = TextFields(QPlainTextEdit(), QPushButton(), QPushButton("Default"), QSpinBox())
    fields.text.textChanged.connect(lambda: setattr(text, "text", fields.text.toPlainText()))
    fields.font_size.setRange(1, 500)
    fields.font_size.valueChanged.connect(lambda value: setattr(text, "font_size", value))

    def pick_color():
        color = QColorDialog.getColor(_text_color(text), inspector.widget)
        if color.isValid():
            text.color = (color.red(), color.green(), color.blue())

    fields.color.clicked.connect(pick_color)
    fields.default_color.setToolTip("Use the theme's text color")
    fields.default_color.clicked.connect(lambda: setattr(text, "color", None))
    color_row = QHBoxLayout()
    color_row.addWidget(fields.color, stretch=1)
    color_row.addWidget(fields.default_color)
    inspector.layout.addWidget(fields.text)
    form = inspector.add_form()
    form.addRow("Font color", color_row)
    form.addRow("Font size", fields.font_size)
    return fields


def refresh_text_inspector(text: Text, fields: TextFields, inspector: Inspector):
    sync_plain_text(fields.text, text.text)
    sync_spin(fields.font_size, text.font_size)
    if text.color != fields.shown_color:
        fields.shown_color = text.color
        swatch = QPixmap(16, 16)
        swatch.fill(_text_color(text))
        fields.color.setIcon(QIcon(swatch))
        fields.color.setText(QColor(*text.color).name() if text.color is not None else "Default")
    fields.default_color.setEnabled(text.color is not None)


def _text_color(text: Text) -> QColor:
    return QColor(*text.color) if text.color is not None else QApplication.palette().color(QPalette.WindowText)


# Images

@dataclass(eq=False)
class ImageFields:
    path: QLineEdit
    status: QLabel


def build_image_inspector(image: Image, inspector: Inspector) -> ImageFields:
    fields = ImageFields(QLineEdit(), QLabel())
    fields.status.setWordWrap(True)
    fields.path.editingFinished.connect(lambda: setattr(image, "path", Path(fields.path.text()).absolute()))

    def browse():
        path = browse_for_image(inspector.widget)
        if path is not None:
            image.path = path.absolute()

    browse_button = QPushButton("Browse...")
    browse_button.clicked.connect(browse)
    inspector.layout.addWidget(QLabel("Path"))
    inspector.layout.addWidget(fields.path)
    inspector.layout.addWidget(browse_button)
    inspector.layout.addWidget(fields.status)
    return fields


def refresh_image_inspector(image: Image, fields: ImageFields, inspector: Inspector):
    sync_line_edit(fields.path, str(image.path))
    sync_label(fields.status, "" if image.path.exists() else "File not found.")


# Programs

@dataclass(eq=False)
class ProgramFields:
    name: QLineEdit
    script: QLabel
    edit_script: QPushButton
    scale: QDoubleSpinBox
    show_log: QCheckBox
    description: QLabel
    parameters: ParameterTable


def build_program_inspector(program: Program, inspector: Inspector) -> ProgramFields:
    fields = ProgramFields(QLineEdit(), QLabel(), QPushButton("Edit Script"), QDoubleSpinBox(), QCheckBox(), QLabel(),
                           build_parameter_table(with_visibility=True))
    fields.name.textEdited.connect(lambda text: setattr(program, "name", text))
    fields.scale.setRange(0.1, 10.0)
    fields.scale.setSingleStep(0.1)
    fields.scale.valueChanged.connect(lambda value: setattr(program, "scale", value))
    fields.show_log.clicked.connect(lambda checked: setattr(program, "show_log", checked))
    fields.description.setWordWrap(True)

    fields.edit_script.setIcon(theme_icon("assets/icons/edit.png"))
    fields.edit_script.clicked.connect(lambda: inspector.edit_script(program.script))
    change = QPushButton(theme_icon("assets/icons/code.png"), "Change Script")
    change.setToolTip("Choose a different script for this program from the script browser.")
    change.clicked.connect(lambda: inspector.choose_script(lambda s: setattr(program, "script", s), program.script))
    script_buttons = QHBoxLayout()
    script_buttons.addWidget(fields.edit_script)
    script_buttons.addWidget(change)

    form = inspector.add_form()
    form.addRow("Name", fields.name)
    form.addRow("Script", fields.script)
    form.addRow("", script_buttons)
    form.addRow("Display scale", fields.scale)
    fields.show_log.setToolTip("Show the message counter beside the program's name, and fold out the log.")
    form.addRow("Show log", fields.show_log)
    inspector.layout.addWidget(fields.description)
    inspector.layout.addWidget(QLabel("<b>Parameters</b>"))
    inspector.layout.addWidget(fields.parameters.widget)
    return fields


def refresh_program_inspector(program: Program, fields: ProgramFields, inspector: Inspector):
    compiled = inspector.runner.compiled_program(program)
    sync_line_edit(fields.name, program.name)
    builtin = program.script.is_builtin()
    sync_label(fields.script, program.script.name() + (" <i>[built-in]</i>" if builtin else ""))
    fields.script.setToolTip("" if builtin else str(program.script.file()))
    exists = program.script.file().exists()
    fields.edit_script.setEnabled(exists and not builtin)
    fields.edit_script.setToolTip("Built-in scripts can't be edited." if builtin else
                                  "Cannot find %s." % program.script.file() if not exists else
                                  "Open this program's script in the script editor.")
    sync_spin(fields.scale, program.scale)
    sync_checked(fields.show_log, program.show_log)
    sync_label(fields.description, compiled.description)
    fields.description.setVisible(bool(compiled.description))
    refresh_parameter_table(fields.parameters, compiled, inspector.session.chip)


INSPECTORS: Dict[type, Tuple[Callable, Callable]] = {
    Valve: (build_valve_inspector, refresh_valve_inspector),
    Text: (build_text_inspector, refresh_text_inspector),
    Image: (build_image_inspector, refresh_image_inspector),
    Program: (build_program_inspector, refresh_program_inspector),
}
