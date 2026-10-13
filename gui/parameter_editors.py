"""Editors for program parameter values, and the parameter tables shown on the canvas and inspector.

A ValueEditor is a widget plus two functions: get() reads the value the user entered, and
show(value, chip) displays a value. Tables are rebuilt only when a program's parameters change
(after a recompile); otherwise each refresh just shows the current values.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
                               QSizePolicy, QSpinBox, QToolButton, QVBoxLayout, QWidget)

from backend import ucscript
from backend.chip import Chip, Program
from backend.programs import CompiledProgram, default_value_for_type, is_list_type, is_options_type
from gui.widgets import clear_layout, sync_checked, sync_combo, sync_line_edit, sync_spin, theme_icon

VISIBLE_ICON = "assets/icons/visible.png"
HIDDEN_ICON = "assets/icons/hidden.png"


@dataclass(eq=False)
class ValueEditor:
    widget: QWidget
    get: Callable[[], Any]
    show: Callable[[Any, Chip], None]


def type_key(t):
    """A comparable description of a parameter type."""
    if isinstance(t, ucscript.OptionsParameterType):
        return "options", tuple(t.options)
    if isinstance(t, ucscript.ListParameterType):
        return "list", type_key(t.listType)
    return getattr(t, "__qualname__", repr(t))


def build_value_editor(t, minimum, maximum, on_change: Callable[[], None]) -> ValueEditor:
    # on_change takes no arguments, so the values Qt signals pass are dropped; the value is read with get().
    if t in (int, float):
        spin = QSpinBox() if t == int else QDoubleSpinBox()
        if minimum is not None:
            spin.setMinimum(minimum)
        if maximum is not None:
            spin.setMaximum(maximum)
        spin.valueChanged.connect(lambda *signal_args: on_change())
        return ValueEditor(spin, spin.value,
                           lambda value, chip: sync_spin(spin, t(value) if isinstance(value, (int, float)) else 0))

    if t == str:
        edit = QLineEdit()
        edit.textEdited.connect(lambda *signal_args: on_change())
        return ValueEditor(edit, edit.text, lambda value, chip: sync_line_edit(edit, str(value)))

    if t == bool:
        box = QCheckBox()
        box.clicked.connect(lambda *signal_args: on_change())
        return ValueEditor(box, box.isChecked, lambda value, chip: sync_checked(box, bool(value)))

    if is_options_type(t):
        combo = QComboBox()
        combo.addItems(t.options)
        combo.activated.connect(lambda *signal_args: on_change())
        return ValueEditor(combo, combo.currentText,
                           lambda value, chip: sync_combo(combo, t.options, combo.findText(str(value))))

    if t in (ucscript.Valve, ucscript.Program):
        # Choose from the chip's valves or programs. [choices] holds the objects shown in the combo.
        combo = QComboBox()
        choices = []
        combo.activated.connect(lambda *signal_args: on_change())

        def show_choice(value, chip: Chip):
            choices[:] = chip.valves if t == ucscript.Valve else chip.programs
            sync_combo(combo, [c.name for c in choices], next((i for i, c in enumerate(choices) if c is value), -1))

        return ValueEditor(combo, lambda: choices[combo.currentIndex()] if 0 <= combo.currentIndex() < len(choices)
                           else None, show_choice)

    if is_list_type(t):
        return _build_list_editor(t, on_change)

    return ValueEditor(QLabel("Unsupported type"), lambda: None, lambda value, chip: None)


def _build_list_editor(t, on_change: Callable[[], None]) -> ValueEditor:
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    items_layout = QVBoxLayout()
    layout.addLayout(items_layout)
    count_layout = QHBoxLayout()
    count_layout.addWidget(QLabel("Count"))
    count = QSpinBox()
    count.setRange(0, 100)
    count.valueChanged.connect(lambda *signal_args: on_change())
    count_layout.addWidget(count, stretch=1)
    layout.addLayout(count_layout)
    children: List[ValueEditor] = []

    def get():
        values = [child.get() for child in children][:count.value()]
        return values + [default_value_for_type(t.listType) for _ in range(count.value() - len(values))]

    def show(value, chip: Chip):
        if len(children) != len(value):
            clear_layout(items_layout)
            children[:] = [build_value_editor(t.listType, None, None, on_change) for _ in value]
            for child in children:
                items_layout.addWidget(child.widget)
        for child, v in zip(children, value):
            child.show(v, chip)
        sync_spin(count, len(value))

    return ValueEditor(widget, get, show)


@dataclass(eq=False)
class ParameterRow:
    symbol: str
    label: QLabel
    editor: ValueEditor
    visibility: Optional[QToolButton] = None


@dataclass(eq=False)
class ParameterTable:
    """Parameter names and editors in a grid. The inspector shows all parameters with visibility
    toggles; the canvas shows only the visible ones."""
    widget: QWidget
    grid: QGridLayout
    with_visibility: bool
    rows: List[ParameterRow] = field(default_factory=list)
    signature: tuple = ()


def build_parameter_table(with_visibility: bool) -> ParameterTable:
    widget = QWidget()
    grid = QGridLayout(widget)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setSpacing(2)
    return ParameterTable(widget, grid, with_visibility)


def _signature(compiled: CompiledProgram) -> tuple:
    return tuple((symbol, type_key(p.parameterType), p.minimum, p.maximum, p.displayName)
                 for symbol, p in compiled.parameters.items())


def _rebuild(table: ParameterTable, compiled: CompiledProgram):
    clear_layout(table.grid)
    table.rows = []
    program = compiled.program
    for i, (symbol, parameter) in enumerate(compiled.parameters.items()):
        def on_change(symbol=symbol):
            row = next(r for r in table.rows if r.symbol == symbol)
            program.parameter_values[symbol] = row.editor.get()

        label = QLabel(parameter.displayName)
        editor = build_value_editor(parameter.parameterType, parameter.minimum, parameter.maximum, on_change)
        editor.widget.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
        row = ParameterRow(symbol, label, editor)
        table.grid.addWidget(label, i, 0)
        table.grid.addWidget(editor.widget, i, 1)
        if table.with_visibility:
            row.visibility = QToolButton()
            row.visibility.setCheckable(True)
            row.visibility.setToolTip("Show on chip")
            row.visibility.clicked.connect(
                lambda checked, symbol=symbol: program.parameter_visibility.__setitem__(symbol, checked))
            table.grid.addWidget(row.visibility, i, 2)
        table.rows.append(row)


_icons = {}


def _visibility_icon(visible: bool):
    if visible not in _icons:
        _icons[visible] = theme_icon(VISIBLE_ICON) if visible else theme_icon(HIDDEN_ICON, dim=True)
    return _icons[visible]


def refresh_parameter_table(table: ParameterTable, compiled: CompiledProgram, chip: Chip):
    signature = _signature(compiled)
    if signature != table.signature:
        _rebuild(table, compiled)
        table.signature = signature
    program: Program = compiled.program
    for row in table.rows:
        visible = program.parameter_visibility.get(row.symbol, True)
        row.editor.show(program.parameter_values.get(row.symbol), chip)
        if row.visibility is not None:
            sync_checked(row.visibility, visible)
            row.visibility.setIcon(_visibility_icon(visible))
        else:
            row.label.setVisible(visible)
            row.editor.widget.setVisible(visible)
    table.widget.setVisible(any(not r.label.isHidden() for r in table.rows))
