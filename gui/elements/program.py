"""How a program is shown and edited.

On the canvas (ProgramView) it is a panel with the program's name, its visible parameters and a row of
controls per function, with a log that folds out to its right. The panel glows green while any of its
functions run (amber while paused). Function controls post their actions to the runner, which runs them
on its thread between ticks.

In the inspector (ProgramInspector) its name, script, display scale, log and all parameters (with their
visibility on the canvas) can be edited.
"""
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple, Union

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPalette
from PySide6.QtWidgets import (QApplication, QCheckBox, QDoubleSpinBox, QFrame, QGraphicsDropShadowEffect,
                               QGraphicsProxyWidget, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QPushButton, QSizePolicy, QStyle, QVBoxLayout, QWidget)

from backend.chip import Chip, Program, Script
from backend.programs import CompiledProgram, MessageKind
from backend.runner import Runner
from gui.elements.styles import AMBER, GREEN, RED, STATE_BUTTON_STYLE, is_dark_theme
from gui.parameter_editors import ParameterTable, build_parameter_table, refresh_parameter_table
from gui.widgets import (add_form, clear_layout, colored_icon, set_visible, sync_checked, sync_label, sync_line_edit,
                         sync_spin, theme_icon)

# Opens the script browser: (on_chosen, initially selected script).
ChooseScript = Callable[[Callable[[Script], None], Optional[Script]], None]

PLAY_ICON = "assets/icons/play.png"
PAUSE_ICON = "assets/icons/pause.png"
STOP_ICON = "assets/icons/stop.png"

# Function names are left-aligned at the same inset, whether on a button or a name label.
FUNCTION_BUTTON_STYLE = "QPushButton { text-align: left; padding-left: 9px; }"
# Labels and colored buttons are inset by a pixel to line up with the theme's buttons, which are drawn
# inside a margin.
NAME_STYLE = "QLabel {{ margin: 1px; border: 1px solid {0}; border-radius: 4px; padding-left: 7px; }}"
NAME_STATE_STYLE = """
QLabel {{ margin: 1px; border: 1px solid {1}; border-radius: 4px; padding-left: 7px; background-color: {0};
         color: white; font-weight: bold; }}
"""
CONTROL_STATE_STYLE = STATE_BUTTON_STYLE + "QPushButton {{ margin: 1px; }}"
# While running, a lighter band sweeps across the name every SWEEP_PERIOD seconds.
SWEEP_PERIOD = 1.6
SWEEP_WIDTH = 0.6  # Of the name's width.
RUNNING_STYLE = NAME_STATE_STYLE + """
QLabel {{ background-color: qlineargradient(x1: {3:.3f}, y1: 0, x2: {4:.3f}, y2: 0,
         stop: 0 {0}, stop: 0.5 {5}, stop: 1 {0}); }}
"""
# The log folds out to the right of the program. The counter beside the program's name shows the number of
# messages (red if any are errors) and folds the log in and out.
LOG_WIDTH = 340
LOG_GAP = 8
LOG_MIN_HEIGHT = 160
COUNTER_STYLE = """
QPushButton {{ background-color: {0}; color: {3}; border: 1px solid {1}; border-radius: 9px; font-weight: bold;
              padding: 1px 8px; }}
QPushButton:hover {{ background-color: {2}; }}
"""


# Canvas: function rows

@dataclass(eq=False)
class FunctionRow:
    """A program function's controls. A one-shot function is a button. A function that yields runs over
    time, so its row is a name label that shows its state, with a run button that is replaced by pause/resume
    and stop buttons while it runs. The row's geometry never changes."""
    symbol: str
    is_async: bool
    name: Union[QPushButton, QLabel]  # The one-shot function's button, or the async function's name.
    run: Optional[QPushButton] = None
    pause: Optional[QPushButton] = None
    stop: Optional[QPushButton] = None
    state: Optional[str] = None  # "idle", "running" or "paused": what the row is styled for.

    def set_name(self, text: str):
        """Sets the function's name and its width, which fits the text in bold (as the state styles draw it),
        whatever the style."""
        if self.name.text() == text:
            return
        self.name.setText(text)
        font = QFont(self.name.font())
        font.setBold(True)
        self.name.setMinimumWidth(QFontMetrics(font).horizontalAdvance(text) + 32)

    def set_state(self, state: str):
        """Styles an async function's row for its state: the name shows it, and only its actions are shown."""
        if state == self.state:
            return
        self.state = state
        # Set directly, rather than with set_visible, as a new row's buttons are not yet shown or hidden.
        self.run.setVisible(state == "idle")
        self.pause.setVisible(state != "idle")
        self.stop.setVisible(state != "idle")
        if state == "idle":
            self.name.setStyleSheet(NAME_STYLE.format(QApplication.palette().color(QPalette.Mid).name()))
        elif state == "paused":
            self.name.setStyleSheet(NAME_STATE_STYLE.format(*AMBER))
        resume = state == "paused"
        self.pause.setToolTip("Resume" if resume else "Pause")
        self.pause.setStyleSheet(CONTROL_STATE_STYLE.format(*(GREEN if resume else AMBER)))
        self.pause.setIcon(colored_icon(PLAY_ICON if resume else PAUSE_ICON, QColor("white")))

    def animate_running(self, now: float):
        """Moves the light band across a running function's name."""
        phase = (now % SWEEP_PERIOD) / SWEEP_PERIOD
        # The band's center goes from fully off the left edge to fully off the right.
        center = -SWEEP_WIDTH / 2 + phase * (1 + SWEEP_WIDTH)
        highlight = QColor(GREEN[0]).lighter(150).name()
        self.name.setStyleSheet(RUNNING_STYLE.format(*GREEN, center - SWEEP_WIDTH / 2, center + SWEEP_WIDTH / 2,
                                                     highlight))


def build_function_row(grid: QGridLayout, index: int, symbol: str, is_async: bool, program: Program,
                       runner: Runner) -> FunctionRow:
    """Adds the row of controls for [program]'s function [symbol] to row [index] of [grid]."""
    # The buttons' actions are posted to the runner, which runs them on its thread between ticks.
    def compiled():
        return runner.get_compiled_program(program)

    def call():
        compiled().call_function(symbol)

    def toggle_paused():
        if compiled().is_function_running(symbol):
            compiled().set_function_paused(symbol, not compiled().is_function_paused(symbol))

    def stop():
        if compiled().is_function_running(symbol):
            compiled().stop_function(symbol)

    # Fixed to the theme's button height (taken before any style sheet), so the state styles can't resize rows.
    height = QPushButton().sizeHint().height()
    if not is_async:
        row = FunctionRow(symbol, False, QPushButton())
        row.name.clicked.connect(lambda: runner.enqueue_command(call, program, symbol))
        row.name.setStyleSheet(FUNCTION_BUTTON_STYLE)
    else:
        row = FunctionRow(symbol, True, QLabel(), QPushButton(), QPushButton(), QPushButton())
        control_width = height + 6
        # Columns are fixed rather than sized from their widgets, as which of them are shown changes.
        grid.setColumnStretch(0, 1)
        grid.setColumnMinimumWidth(1, control_width)
        grid.setColumnMinimumWidth(2, control_width)
        # The run button takes the place of both pause and stop.
        row.run.setFixedSize(2 * control_width + grid.horizontalSpacing(), height)
        row.run.setIcon(colored_icon(PLAY_ICON, QColor(GREEN[2])))
        row.run.setToolTip("Run")
        row.run.clicked.connect(lambda: runner.enqueue_command(call, program, symbol))
        for button in (row.pause, row.stop):
            button.setFixedSize(control_width, height)
        row.stop.setToolTip("Stop")
        row.stop.setStyleSheet(CONTROL_STATE_STYLE.format(*RED))
        row.stop.setIcon(colored_icon(STOP_ICON, QColor("white")))
        row.pause.clicked.connect(lambda: runner.enqueue_command(toggle_paused, program, symbol))
        row.stop.clicked.connect(lambda: runner.enqueue_command(stop, program, symbol))
        grid.addWidget(row.run, index, 1, 1, 2)
        grid.addWidget(row.pause, index, 1)
        grid.addWidget(row.stop, index, 2)
    # The width comes from the text alone (see set_name), not the size hint, which changes with the state
    # styles.
    row.name.setFixedHeight(height)
    row.name.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
    grid.addWidget(row.name, index, 0, 1, 1 if is_async else 3)
    return row


# Canvas: the program view

@dataclass(eq=False)
class ProgramView:
    program: Program
    chip: Chip
    runner: Runner
    frame: QFrame
    name: QLabel
    parameters: ParameterTable
    functions_grid: QGridLayout
    counter: QPushButton
    log_proxy: QGraphicsProxyWidget  # The log panel, a child of the program's proxy so it moves with it.
    log_panel: QFrame
    messages: QListWidget
    shadow: QGraphicsDropShadowEffect  # On the program's proxy; it glows while running.
    functions: List[FunctionRow] = field(default_factory=list)
    state: Optional[str] = None  # None, "running" or "paused": what the shadow shows.
    log_open: bool = False
    # Messages as of the last refresh. The log opens by itself when the first message arrives.
    message_count: int = 0
    messages_key: tuple = ()
    counter_key: tuple = ()

    @property
    def widget(self) -> QWidget:
        return self.frame

    def attach(self, proxy: QGraphicsProxyWidget):
        """Puts the shadow and the log on the proxy showing the program, so they move with it."""
        proxy.setGraphicsEffect(self.shadow)
        self.log_proxy.setParentItem(proxy)

    def refresh(self):
        compiled = self.runner.get_compiled_program(self.program)
        sync_label(self.name, self.program.name)
        refresh_parameter_table(self.parameters, compiled, self.chip)
        self._refresh_functions(compiled)
        self._refresh_log(list(compiled.messages))  # Copied, as running functions add to it on the runner thread.

    def _refresh_functions(self, compiled: CompiledProgram):
        functions = [(symbol, compiled.is_function_async(symbol)) for symbol in compiled.showable_functions]
        if [(row.symbol, row.is_async) for row in self.functions] != functions:
            clear_layout(self.functions_grid)
            self.functions = [build_function_row(self.functions_grid, i, symbol, is_async, self.program, self.runner)
                              for i, (symbol, is_async) in enumerate(functions)]
        now = time.time()
        for row in self.functions:
            row.set_name(compiled.functions[row.symbol].functionName)
            if not row.is_async:
                continue
            running = compiled.running.get(row.symbol)
            row.set_state("idle" if running is None else "paused" if running.paused else "running")
            if row.state == "running":
                row.animate_running(now)

        states = [row.state for row in self.functions]
        state = "running" if "running" in states else "paused" if "paused" in states else None
        if state != self.state:
            self.state = state
            _set_shadow(self.shadow, state)

    def _refresh_log(self, messages: list):
        """Updates the counter and the log, opening the log when its first message arrives."""
        count = len(messages)
        errors = sum(m.kind != MessageKind.LOG for m in messages)
        if not self.program.show_log:
            self.log_open = False
        elif self.message_count == 0 and count > 0:
            self.log_open = True
        self.message_count = count
        set_visible([self.counter], self.program.show_log)
        self._refresh_counter(count, errors)

        key = (id(messages[0]) if messages else None, count)
        if key != self.messages_key:
            self.messages_key = key
            self.messages.clear()
            error_icon = QApplication.style().standardIcon(QStyle.SP_MessageBoxCritical)
            for message in messages:
                entry = QListWidgetItem(message.text)
                if message.kind != MessageKind.LOG:
                    entry.setIcon(error_icon)
                self.messages.addItem(entry)
            self.messages.scrollToBottom()

        self.frame.adjustSize()
        if self.log_proxy.isVisible() != self.log_open:
            self.log_proxy.setVisible(self.log_open)
        if self.log_open:
            position = QPointF(self.frame.width() + LOG_GAP, 0)
            if self.log_proxy.pos() != position:
                self.log_proxy.setPos(position)
            height = max(self.frame.height(), LOG_MIN_HEIGHT)
            if self.log_panel.height() != height:
                self.log_panel.setFixedHeight(height)

    def _refresh_counter(self, count: int, errors: int):
        key = (count, errors, self.log_open)
        if key == self.counter_key:
            return
        self.counter_key = key
        self.counter.setText("%d %s" % (count, "◂" if self.log_open else "▸"))
        palette = QApplication.palette()
        if errors:
            style = COUNTER_STYLE.format(*RED, "white")
        elif count:
            highlight = palette.color(QPalette.Highlight)
            style = COUNTER_STYLE.format(highlight.name(), highlight.darker(130).name(), highlight.lighter(115).name(),
                                         palette.color(QPalette.HighlightedText).name())
        else:
            style = COUNTER_STYLE.format("transparent", palette.color(QPalette.Mid).name(),
                                         palette.color(QPalette.Midlight).name(),
                                         palette.color(QPalette.PlaceholderText).name())
        self.counter.setStyleSheet(style)
        summary = "%d error%s, %d message%s" % (errors, "" if errors == 1 else "s", count - errors,
                                                "" if count - errors == 1 else "s")
        self.counter.setToolTip(summary + (". Click to hide the log." if self.log_open else ". Click to show the log."))
        # Keeps the centered name clear of the counter.
        width = self.counter.sizeHint().width() + 4
        self.name.setContentsMargins(width, 0, width, 0)


def build_program_view(program: Program, chip: Chip, runner: Runner) -> ProgramView:
    frame = _panel()
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(8, 6, 8, 8)
    layout.setSpacing(6)

    # The name is centered across the whole header, with the counter over its right end.
    name = QLabel()
    name.setAlignment(Qt.AlignCenter)
    font = QFont(name.font())
    font.setBold(True)
    font.setPointSizeF(font.pointSizeF() * 1.15)
    name.setFont(font)
    counter = QPushButton()
    counter.setCursor(Qt.PointingHandCursor)
    header = QGridLayout()
    header.setContentsMargins(0, 0, 0, 0)
    header.addWidget(name, 0, 0)
    header.addWidget(counter, 0, 0, Qt.AlignRight | Qt.AlignVCenter)
    layout.addLayout(header)
    layout.addWidget(_separator())

    parameters = build_parameter_table(with_visibility=False)
    layout.addWidget(parameters.widget)

    functions_widget = QWidget()
    functions_grid = QGridLayout(functions_widget)
    functions_grid.setContentsMargins(0, 0, 0, 0)
    functions_grid.setSpacing(4)
    layout.addWidget(functions_widget)

    log_panel, messages, clear = _build_log_panel()
    log_proxy = QGraphicsProxyWidget()
    log_proxy.setWidget(log_panel)
    log_proxy.setVisible(False)

    shadow = QGraphicsDropShadowEffect()
    _set_shadow(shadow, None)
    view = ProgramView(program, chip, runner, frame, name, parameters, functions_grid, counter, log_proxy, log_panel,
                       messages, shadow)

    def toggle_log():
        view.log_open = not view.log_open

    def clear_log():
        runner.enqueue_command(lambda: runner.get_compiled_program(program).clear_messages())
        view.log_open = False

    counter.clicked.connect(toggle_log)
    clear.clicked.connect(clear_log)
    return view


def _panel() -> QFrame:
    """A panel a shade darker than the theme's window color, so it stands out from the canvas."""
    frame = QFrame()
    frame.setFrameShape(QFrame.StyledPanel)
    frame.setAutoFillBackground(True)
    palette = frame.palette()
    palette.setColor(QPalette.Window, palette.color(QPalette.Window).darker(150 if is_dark_theme() else 108))
    frame.setPalette(palette)
    return frame


def _separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line


def _build_log_panel() -> Tuple[QFrame, QListWidget, QPushButton]:
    panel = _panel()
    panel.setFixedWidth(LOG_WIDTH)
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(8, 6, 8, 8)
    layout.setSpacing(6)
    header = QHBoxLayout()
    title = QLabel("Log")
    font = QFont(title.font())
    font.setBold(True)
    title.setFont(font)
    clear = QPushButton("Clear")
    clear.setToolTip("Clear the log and hide it. The next message opens it again.")
    header.addWidget(title, stretch=1)
    header.addWidget(clear)
    messages = QListWidget()
    messages.setWordWrap(True)
    messages.setAlternatingRowColors(True)
    messages.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    layout.addLayout(header)
    layout.addWidget(messages, stretch=1)
    return panel, messages, clear


def _set_shadow(shadow: QGraphicsDropShadowEffect, state: Optional[str]):
    """A soft drop shadow, or a green (running) or amber (paused) glow."""
    if state is None:
        shadow.setColor(QColor(0, 0, 0, 160 if is_dark_theme() else 90))
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 3)
    else:
        shadow.setColor(QColor((GREEN if state == "running" else AMBER)[0]))
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 0)


# Inspector

@dataclass(eq=False)
class ProgramInspector:
    program: Program
    chip: Chip
    runner: Runner
    name: QLineEdit
    script: QLabel
    edit_script: QPushButton
    scale: QDoubleSpinBox
    show_log: QCheckBox
    description: QLabel
    parameters: ParameterTable

    def refresh(self):
        program = self.program
        compiled = self.runner.get_compiled_program(program)
        sync_line_edit(self.name, program.name)
        builtin = program.script.is_builtin()
        sync_label(self.script, program.script.name() + (" <i>[built-in]</i>" if builtin else ""))
        self.script.setToolTip("" if builtin else str(program.script.file()))
        exists = program.script.file().exists()
        self.edit_script.setEnabled(exists and not builtin)
        self.edit_script.setToolTip("Built-in scripts can't be edited." if builtin else
                                    "Cannot find %s." % program.script.file() if not exists else
                                    "Open this program's script in the script editor.")
        sync_spin(self.scale, program.scale)
        sync_checked(self.show_log, program.show_log)
        sync_label(self.description, compiled.description)
        self.description.setVisible(bool(compiled.description))
        refresh_parameter_table(self.parameters, compiled, self.chip)


def build_program_inspector(program: Program, layout: QVBoxLayout, chip: Chip, runner: Runner,
                            choose_script: ChooseScript, edit_script: Callable[[Script], None]) -> ProgramInspector:
    inspector = ProgramInspector(program, chip, runner, QLineEdit(), QLabel(), QPushButton("Edit Script"),
                                 QDoubleSpinBox(), QCheckBox(), QLabel(), build_parameter_table(with_visibility=True))
    inspector.name.textEdited.connect(lambda text: setattr(program, "name", text))
    inspector.scale.setRange(0.1, 10.0)
    inspector.scale.setSingleStep(0.1)
    inspector.scale.valueChanged.connect(lambda value: setattr(program, "scale", value))
    inspector.show_log.clicked.connect(lambda checked: setattr(program, "show_log", checked))
    inspector.description.setWordWrap(True)

    inspector.edit_script.setIcon(theme_icon("assets/icons/edit.png"))
    inspector.edit_script.clicked.connect(lambda: edit_script(program.script))
    change = QPushButton(theme_icon("assets/icons/code.png"), "Change Script")
    change.setToolTip("Choose a different script for this program from the script browser.")
    change.clicked.connect(lambda: choose_script(lambda s: setattr(program, "script", s), program.script))
    script_buttons = QHBoxLayout()
    script_buttons.addWidget(inspector.edit_script)
    script_buttons.addWidget(change)

    form = add_form(layout)
    form.addRow("Name", inspector.name)
    form.addRow("Script", inspector.script)
    form.addRow("", script_buttons)
    form.addRow("Display scale", inspector.scale)
    inspector.show_log.setToolTip("Show the message counter beside the program's name, and fold out the log.")
    form.addRow("Show log", inspector.show_log)
    layout.addWidget(inspector.description)
    layout.addWidget(QLabel("<b>Parameters</b>"))
    layout.addWidget(inspector.parameters.widget)
    return inspector
