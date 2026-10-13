"""Small helpers shared by the GUI modules.

The GUI refreshes widgets from the session on a timer. The sync_* helpers update a widget only when
its value differs and the user isn't editing it, with signals blocked so a refresh never echoes back
as an edit.
"""
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

from PySide6.QtCore import QEvent, QObject, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPalette, QPixmap
from PySide6.QtWidgets import (QAbstractButton, QAbstractSpinBox, QApplication, QComboBox, QFileDialog, QLabel, QLayout,
                               QLineEdit, QPlainTextEdit, QWidget)

APP_ICON_FILE = "assets/icons/uchip.png"


class EventHook(QObject):
    """Calls handlers for events on a watched object, so plain widgets can react to events (close,
    paint, ...) without being subclassed. A handler returns True to consume the event."""

    def __init__(self, watched: QObject, handlers: Dict[QEvent.Type, Callable[[QEvent], bool]]):
        super().__init__(watched)
        self.handlers = handlers
        watched.installEventFilter(self)

    def eventFilter(self, watched, event) -> bool:
        handler = self.handlers.get(event.type())
        return bool(handler(event)) if handler is not None else False


def browse_for_image(parent: QWidget) -> Optional[Path]:
    path, _ = QFileDialog.getOpenFileName(parent, "Browse for image", filter="Images (*.png *.bmp *.gif *.jpg *.jpeg)")
    return Path(path) if path else None


def theme_icon(path: str, dim: bool = False) -> QIcon:
    """The icon at [path] drawn in the theme's text color (or its placeholder color, if [dim])."""
    palette = QApplication.palette()
    return colored_icon(path, palette.color(QPalette.PlaceholderText if dim else QPalette.WindowText))


def colored_icon(path: str, color: QColor) -> QIcon:
    """The icon at [path] with all opaque pixels filled with [color]."""
    pixmap = QPixmap(path)
    colored = QPixmap(pixmap.size())
    colored.fill(color)
    colored.setMask(pixmap.createMaskFromColor(Qt.transparent))
    return QIcon(colored)


def autofit_font(font: QFont, size: QSize, text: str) -> QFont:
    """A copy of [font] sized so [text] fills [size]."""
    font = QFont(font)
    font.setPixelSize(16)
    text_size = QFontMetrics(font).boundingRect(text).size()
    if text_size.width() <= 0 or text_size.height() <= 0:
        return font
    scale = min(size.width() / text_size.width(), size.height() / text_size.height())
    font.setPixelSize(max(1, round(16 * scale)))
    return font


def clear_layout(layout: QLayout):
    while layout.count():
        entry = layout.takeAt(0)
        widget = entry.widget()
        if widget is not None:
            # Hide now so it disappears immediately; deleteLater only frees it on the next event loop pass.
            widget.hide()
            widget.deleteLater()
        elif entry.layout() is not None:
            clear_layout(entry.layout())


def sync_label(label: QLabel, text: str):
    if label.text() != text:
        label.setText(text)


def sync_line_edit(edit: QLineEdit, text: str):
    if edit.text() != text and not edit.hasFocus():
        edit.blockSignals(True)
        edit.setText(text)
        edit.blockSignals(False)


def sync_plain_text(edit: QPlainTextEdit, text: str):
    if edit.toPlainText() != text and not edit.hasFocus():
        edit.blockSignals(True)
        edit.setPlainText(text)
        edit.blockSignals(False)


def sync_spin(spin: QAbstractSpinBox, value):
    if spin.value() != value and not spin.hasFocus():
        spin.blockSignals(True)
        spin.setValue(value)
        spin.blockSignals(False)


def sync_checked(button: QAbstractButton, checked: bool):
    if button.isChecked() != checked:
        button.blockSignals(True)
        button.setChecked(checked)
        button.blockSignals(False)


def sync_combo(combo: QComboBox, names: Sequence[str], index: int):
    combo.blockSignals(True)
    if [combo.itemText(i) for i in range(combo.count())] != list(names):
        combo.clear()
        combo.addItems(list(names))
    if combo.currentIndex() != index:
        combo.setCurrentIndex(index)
    combo.blockSignals(False)


def set_visible(widgets: List[QWidget], visible: bool):
    for widget in widgets:
        if widget.isHidden() == visible:
            widget.setVisible(visible)
