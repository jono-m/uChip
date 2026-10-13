"""The widgets that show chip elements (valves, text, images, programs) on the canvas.

Each element type has a build function, returning its widget and a 'parts' record of the widgets it
needs to update, and a refresh function that updates those widgets from the element's data.

Widgets use the system theme. The only custom colors are states: valves open/closed, and running or
paused program functions.
"""
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPalette, QPixmap
from PySide6.QtWidgets import (QApplication, QFrame, QGraphicsDropShadowEffect, QGraphicsProxyWidget,
                               QGraphicsRectItem, QGridLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QPushButton, QSizePolicy, QStyle, QVBoxLayout, QWidget)

from backend.chip import Element, Image, Program, Text, Valve
from backend.programs import MessageKind
from backend.runner import Runner
from backend.session import Session
from gui.parameter_editors import ParameterTable, build_parameter_table, refresh_parameter_table
from gui.widgets import autofit_font, clear_layout, colored_icon, set_visible, sync_label, theme_icon

# State colors, the same in light and dark themes: (fill, border/pressed, hover).
GREEN = ("#2e8b57", "#1f5f3b", "#36a165")
RED = ("#b3383c", "#7d2729", "#c74448")
AMBER = ("#c98a1b", "#8f6213", "#dd9a23")

STATE_BUTTON_STYLE = """
QPushButton {{ background-color: {0}; color: white; border: 1px solid {1}; border-radius: 4px; font-weight: bold;
              padding: 3px 8px; }}
QPushButton:hover {{ background-color: {2}; }}
QPushButton:pressed {{ background-color: {1}; }}
"""
VALVE_OPEN_STYLE = STATE_BUTTON_STYLE.format(*GREEN)
VALVE_CLOSED_STYLE = STATE_BUTTON_STYLE.format(*RED)


@dataclass(eq=False)
class CanvasElement:
    element: Element
    proxy: QGraphicsProxyWidget
    border: QGraphicsRectItem
    parts: Any

    def rect(self) -> QRectF:
        return self.proxy.sceneBoundingRect()


def set_element_rect(element: Element, rect: QRectF):
    """Stores a moved/resized rect on the element. Programs size themselves, so only move."""
    # Rounded so snapped positions don't carry floating point noise into saved files.
    x, y, w, h = (round(v, 3) for v in (rect.x(), rect.y(), rect.width(), rect.height()))
    if isinstance(element, Program):
        element.position = [x, y]
    else:
        element.rect = [x, y, w, h]


def is_resizable(element: Element) -> bool:
    return not isinstance(element, Program)


def _standard_icon(icon: QStyle.StandardPixmap):
    return QApplication.style().standardIcon(icon)


def _is_dark_theme() -> bool:
    return QApplication.palette().color(QPalette.Window).lightness() < 128


# Valves

@dataclass(eq=False)
class ValveParts:
    button: QPushButton
    is_open: Optional[bool] = None


def build_valve(valve: Valve, session: Session, runner: Runner) -> Tuple[QWidget, ValveParts]:
    button = QPushButton()
    button.setMinimumSize(1, 1)
    button.clicked.connect(lambda: session.rig.toggle_solenoid(valve.solenoid))
    return button, ValveParts(button)


def refresh_valve(valve: Valve, parts: ValveParts, session: Session, runner: Runner):
    button = parts.button
    text = "%s\n(%d)" % (valve.name, valve.solenoid)
    if button.text() != text:
        button.setText(text)
    font = autofit_font(button.font(), QSize(button.width(), button.height() // 2), text)
    if font.pixelSize() != button.font().pixelSize():
        button.setFont(font)
    is_open = session.rig.get_solenoid(valve.solenoid)
    if is_open != parts.is_open:
        parts.is_open = is_open
        button.setStyleSheet(VALVE_OPEN_STYLE if is_open else VALVE_CLOSED_STYLE)


# Text

@dataclass(eq=False)
class TextParts:
    label: QLabel


def build_text(text: Text, session: Session, runner: Runner) -> Tuple[QWidget, TextParts]:
    label = QLabel()
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    label.setMinimumSize(1, 1)
    label.setAttribute(Qt.WA_TranslucentBackground)
    return label, TextParts(label)


def refresh_text(text: Text, parts: TextParts, session: Session, runner: Runner):
    label = parts.label
    sync_label(label, text.text)
    if label.font().pixelSize() != text.font_size:
        font = QFont(label.font())
        font.setPixelSize(text.font_size)
        label.setFont(font)
    # No color means the theme's text color.
    color = QColor(*text.color) if text.color is not None else QApplication.palette().color(QPalette.WindowText)
    if label.palette().color(QPalette.WindowText) != color:
        palette = label.palette()
        palette.setColor(QPalette.WindowText, color)
        label.setPalette(palette)


# Images

@dataclass(eq=False)
class ImageParts:
    label: QLabel
    loaded: Optional[tuple] = None  # (path, modification time) of the shown image


def _mtime(path: Path) -> Optional[float]:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def build_image(image: Image, session: Session, runner: Runner) -> Tuple[QWidget, ImageParts]:
    label = QLabel()
    label.setScaledContents(True)
    label.setAlignment(Qt.AlignCenter)
    label.setWordWrap(True)
    label.setMinimumSize(1, 1)
    label.setAttribute(Qt.WA_TranslucentBackground)
    return label, ImageParts(label)


def refresh_image(image: Image, parts: ImageParts, session: Session, runner: Runner):
    key = (image.path, _mtime(image.path))
    if key == parts.loaded:
        return
    parts.loaded = key
    pixmap = QPixmap(str(image.path))
    if pixmap.isNull():
        parts.label.setPixmap(QPixmap())
        parts.label.setText("Image not found:\n%s" % image.path)
        parts.label.setFrameShape(QFrame.StyledPanel)
    else:
        parts.label.setFrameShape(QFrame.NoFrame)
        parts.label.setPixmap(pixmap)


# Programs

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


@dataclass(eq=False)
class ProgramParts:
    frame: QFrame
    name: QLabel
    parameters: ParameterTable
    functions_grid: QGridLayout
    counter: QPushButton
    log_proxy: QGraphicsProxyWidget  # The log panel, a child of the program's proxy so it moves with it.
    log_panel: QFrame
    messages: QListWidget
    functions: List[FunctionRow] = field(default_factory=list)
    messages_key: tuple = ()
    log_open: bool = False
    # Messages as of the last refresh. The log opens by itself when the first message arrives.
    message_count: int = 0
    counter_key: tuple = ()
    shadow: QGraphicsDropShadowEffect = None
    state: Optional[str] = None  # None, "running" or "paused": what the shadow shows.


def _separator() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line


def _panel() -> QFrame:
    """A panel a shade darker than the theme's window color, so it stands out from the canvas."""
    frame = QFrame()
    frame.setFrameShape(QFrame.StyledPanel)
    frame.setAutoFillBackground(True)
    palette = frame.palette()
    palette.setColor(QPalette.Window, palette.color(QPalette.Window).darker(150 if _is_dark_theme() else 108))
    frame.setPalette(palette)
    return frame


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


def build_program(program: Program, session: Session, runner: Runner) -> Tuple[QWidget, ProgramParts]:
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

    # The canvas element's proxy gets this shadow (see build_canvas_element); it glows while running.
    shadow = QGraphicsDropShadowEffect()
    _set_shadow(shadow, None)
    parts = ProgramParts(frame, name, parameters, functions_grid, counter, log_proxy, log_panel, messages,
                         shadow=shadow)

    def toggle_log():
        parts.log_open = not parts.log_open

    def clear_log():
        runner.compiled_program(program).clear_messages()
        parts.log_open = False

    counter.clicked.connect(toggle_log)
    clear.clicked.connect(clear_log)
    return frame, parts


def _set_shadow(shadow: QGraphicsDropShadowEffect, state: Optional[str]):
    if state is None:
        shadow.setColor(QColor(0, 0, 0, 160 if _is_dark_theme() else 90))
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 3)
    else:
        shadow.setColor(QColor((GREEN if state == "running" else AMBER)[0]))
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 0)


def _build_function_row(parts: ProgramParts, index: int, symbol: str, is_async: bool, runner: Runner,
                        program: Program):
    def compiled():
        return runner.compiled_program(program)

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
        row.name.clicked.connect(lambda: compiled().call_function(symbol))
        row.name.setStyleSheet(FUNCTION_BUTTON_STYLE)
    else:
        row = FunctionRow(symbol, True, QLabel(), QPushButton(), QPushButton(), QPushButton())
        control_width = height + 6
        # Columns are fixed rather than sized from their widgets, as which of them are shown changes.
        grid = parts.functions_grid
        grid.setColumnStretch(0, 1)
        grid.setColumnMinimumWidth(1, control_width)
        grid.setColumnMinimumWidth(2, control_width)
        # The run button takes the place of both pause and stop.
        row.run.setFixedSize(2 * control_width + parts.functions_grid.horizontalSpacing(), height)
        row.run.setIcon(colored_icon(PLAY_ICON, QColor(GREEN[2])))
        row.run.setToolTip("Run")
        row.run.clicked.connect(lambda: compiled().call_function(symbol))
        for button in (row.pause, row.stop):
            button.setFixedSize(control_width, height)
        row.stop.setToolTip("Stop")
        row.stop.setStyleSheet(CONTROL_STATE_STYLE.format(*RED))
        row.stop.setIcon(colored_icon(STOP_ICON, QColor("white")))
        row.pause.clicked.connect(toggle_paused)
        row.stop.clicked.connect(stop)
        parts.functions_grid.addWidget(row.run, index, 1, 1, 2)
        parts.functions_grid.addWidget(row.pause, index, 1)
        parts.functions_grid.addWidget(row.stop, index, 2)
    # The width comes from the text alone (see _sync_function_text), not the size hint, which changes with
    # the state styles.
    row.name.setFixedHeight(height)
    row.name.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
    parts.functions_grid.addWidget(row.name, index, 0, 1, 1 if is_async else 3)
    parts.functions.append(row)


def _style_function_row(row: FunctionRow, state: str):
    """Styles an async function's row for its state: the name shows it, and only its actions are shown."""
    # Set directly, rather than with set_visible, as a new row's buttons are not yet shown or hidden.
    row.run.setVisible(state == "idle")
    row.pause.setVisible(state != "idle")
    row.stop.setVisible(state != "idle")
    if state == "idle":
        row.name.setStyleSheet(NAME_STYLE.format(QApplication.palette().color(QPalette.Mid).name()))
    elif state == "paused":
        row.name.setStyleSheet(NAME_STATE_STYLE.format(*AMBER))
    resume = state == "paused"
    row.pause.setToolTip("Resume" if resume else "Pause")
    row.pause.setStyleSheet(CONTROL_STATE_STYLE.format(*(GREEN if resume else AMBER)))
    row.pause.setIcon(colored_icon(PLAY_ICON if resume else PAUSE_ICON, QColor("white")))


def _animate_running(row: FunctionRow, now: float):
    """Moves the light band across a running function's name."""
    phase = (now % SWEEP_PERIOD) / SWEEP_PERIOD
    # The band's center goes from fully off the left edge to fully off the right.
    center = -SWEEP_WIDTH / 2 + phase * (1 + SWEEP_WIDTH)
    highlight = QColor(GREEN[0]).lighter(150).name()
    row.name.setStyleSheet(RUNNING_STYLE.format(*GREEN, center - SWEEP_WIDTH / 2, center + SWEEP_WIDTH / 2,
                                                highlight))


def _sync_function_text(name: Union[QPushButton, QLabel], text: str):
    """Sets a function's name and its width, which fits the text in bold (as the state styles draw it),
    whatever the style."""
    if name.text() == text:
        return
    name.setText(text)
    font = QFont(name.font())
    font.setBold(True)
    name.setMinimumWidth(QFontMetrics(font).horizontalAdvance(text) + 32)


def refresh_program(program: Program, parts: ProgramParts, session: Session, runner: Runner):
    compiled = runner.compiled_program(program)
    sync_label(parts.name, program.name)
    refresh_parameter_table(parts.parameters, compiled, session.chip)

    functions = [(symbol, compiled.is_function_async(symbol)) for symbol in compiled.showable_functions]
    if [(row.symbol, row.is_async) for row in parts.functions] != functions:
        clear_layout(parts.functions_grid)
        parts.functions = []
        for i, (symbol, is_async) in enumerate(functions):
            _build_function_row(parts, i, symbol, is_async, runner, program)
    now = time.time()
    for row in parts.functions:
        _sync_function_text(row.name, compiled.functions[row.symbol].functionName)
        if not row.is_async:
            continue
        running = compiled.running.get(row.symbol)
        state = "idle" if running is None else "paused" if running.paused else "running"
        if state != row.state:
            row.state = state
            _style_function_row(row, state)
        if state == "running":
            _animate_running(row, now)

    states = [row.state for row in parts.functions]
    state = "running" if "running" in states else "paused" if "paused" in states else None
    if state != parts.state:
        parts.state = state
        _set_shadow(parts.shadow, state)

    refresh_program_log(program, parts, compiled.messages)


def _sync_counter(parts: ProgramParts, count: int, errors: int):
    key = (count, errors, parts.log_open)
    if key == parts.counter_key:
        return
    parts.counter_key = key
    counter = parts.counter
    counter.setText("%d %s" % (count, "\u25c2" if parts.log_open else "\u25b8"))
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
    counter.setStyleSheet(style)
    summary = "%d error%s, %d message%s" % (errors, "" if errors == 1 else "s", count - errors,
                                            "" if count - errors == 1 else "s")
    counter.setToolTip(summary + (". Click to hide the log." if parts.log_open else ". Click to show the log."))
    # Keeps the centered name clear of the counter.
    width = counter.sizeHint().width() + 4
    parts.name.setContentsMargins(width, 0, width, 0)


def refresh_program_log(program: Program, parts: ProgramParts, messages: list):
    """Updates the counter and the log, opening the log when its first message arrives."""
    messages = list(messages)  # Copied, as running functions add to it on the runner thread.
    count = len(messages)
    errors = sum(m.kind != MessageKind.LOG for m in messages)
    if not program.show_log:
        parts.log_open = False
    elif parts.message_count == 0 and count > 0:
        parts.log_open = True
    parts.message_count = count
    set_visible([parts.counter], program.show_log)
    _sync_counter(parts, count, errors)

    key = (id(messages[0]) if messages else None, count)
    if key != parts.messages_key:
        parts.messages_key = key
        parts.messages.clear()
        error_icon = _standard_icon(QStyle.SP_MessageBoxCritical)
        for message in messages:
            entry = QListWidgetItem(message.text)
            if message.kind != MessageKind.LOG:
                entry.setIcon(error_icon)
            parts.messages.addItem(entry)
        parts.messages.scrollToBottom()

    parts.frame.adjustSize()
    proxy = parts.log_proxy
    if proxy.isVisible() != parts.log_open:
        proxy.setVisible(parts.log_open)
    if parts.log_open:
        position = QPointF(parts.frame.width() + LOG_GAP, 0)
        if proxy.pos() != position:
            proxy.setPos(position)
        height = max(parts.frame.height(), LOG_MIN_HEIGHT)
        if parts.log_panel.height() != height:
            parts.log_panel.setFixedHeight(height)


# Dispatch by element type: (build, refresh)
ELEMENT_TYPES: Dict[type, Tuple[Callable, Callable]] = {
    Valve: (build_valve, refresh_valve),
    Text: (build_text, refresh_text),
    Image: (build_image, refresh_image),
    Program: (build_program, refresh_program),
}


def build_canvas_element(element: Element, session: Session, runner: Runner) -> CanvasElement:
    build, _ = ELEMENT_TYPES[type(element)]
    widget, parts = build(element, session, runner)
    proxy = QGraphicsProxyWidget()
    proxy.setWidget(widget)
    if isinstance(parts, ProgramParts):
        proxy.setGraphicsEffect(parts.shadow)
        parts.log_proxy.setParentItem(proxy)
    return CanvasElement(element, proxy, QGraphicsRectItem(), parts)


def refresh_canvas_element(canvas_element: CanvasElement, session: Session, runner: Runner, editing: bool):
    _, refresh = ELEMENT_TYPES[type(canvas_element.element)]
    # In edit mode the canvas takes all mouse input itself; widgets stay at full color but don't
    # react to hovering or take keyboard focus.
    proxy = canvas_element.proxy
    if proxy.acceptHoverEvents() == editing:
        # Includes fold-outs attached to the element, such as a program's log.
        for item in [proxy, *proxy.childItems()]:
            if isinstance(item, QGraphicsProxyWidget):
                item.setAcceptHoverEvents(not editing)
                item.widget().setAttribute(Qt.WA_TransparentForMouseEvents, editing)
                if editing:
                    item.clearFocus()
    refresh(canvas_element.element, canvas_element.parts, session, runner)

    element = canvas_element.element
    if isinstance(element, Program):
        position, size, scale = element.position, None, element.scale
    else:
        position, size, scale = element.rect[:2], element.rect[2:], 1.0
    if (proxy.pos().x(), proxy.pos().y()) != tuple(position):
        proxy.setPos(*position)
    if proxy.scale() != scale:
        proxy.setScale(scale)
    if size is not None and (proxy.size().width(), proxy.size().height()) != tuple(size):
        proxy.resize(*size)
