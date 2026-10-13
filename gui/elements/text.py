"""How a text element is shown and edited.

On the canvas (TextView) it is a label in the text's font size and color. In the inspector
(TextInspector) the text, font size and color can be edited. No color means the theme's text color.
"""
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPalette, QPixmap
from PySide6.QtWidgets import (QApplication, QColorDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSpinBox,
                               QVBoxLayout, QWidget)

from backend.chip import Text
from gui.widgets import add_form, sync_label, sync_plain_text, sync_spin


def text_color(text: Text) -> QColor:
    return QColor(*text.color) if text.color is not None else QApplication.palette().color(QPalette.WindowText)


# Canvas

@dataclass(eq=False)
class TextView:
    text: Text
    label: QLabel

    @property
    def widget(self) -> QWidget:
        return self.label

    def refresh(self):
        sync_label(self.label, self.text.text)
        if self.label.font().pixelSize() != self.text.font_size:
            font = QFont(self.label.font())
            font.setPixelSize(self.text.font_size)
            self.label.setFont(font)
        color = text_color(self.text)
        if self.label.palette().color(QPalette.WindowText) != color:
            palette = self.label.palette()
            palette.setColor(QPalette.WindowText, color)
            self.label.setPalette(palette)


def build_text_view(text: Text) -> TextView:
    label = QLabel()
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    label.setMinimumSize(1, 1)
    label.setAttribute(Qt.WA_TranslucentBackground)
    return TextView(text, label)


# Inspector

@dataclass(eq=False)
class TextInspector:
    text: Text
    edit: QPlainTextEdit
    color: QPushButton
    default_color: QPushButton
    font_size: QSpinBox
    shown_color: object = None  # The color the color button shows.

    def refresh(self):
        sync_plain_text(self.edit, self.text.text)
        sync_spin(self.font_size, self.text.font_size)
        if self.text.color != self.shown_color:
            self.shown_color = self.text.color
            swatch = QPixmap(16, 16)
            swatch.fill(text_color(self.text))
            self.color.setIcon(QIcon(swatch))
            self.color.setText(QColor(*self.text.color).name() if self.text.color is not None else "Default")
        self.default_color.setEnabled(self.text.color is not None)


def build_text_inspector(text: Text, layout: QVBoxLayout) -> TextInspector:
    inspector = TextInspector(text, QPlainTextEdit(), QPushButton(), QPushButton("Default"), QSpinBox())
    inspector.edit.textChanged.connect(lambda: setattr(text, "text", inspector.edit.toPlainText()))
    inspector.font_size.setRange(1, 500)
    inspector.font_size.valueChanged.connect(lambda value: setattr(text, "font_size", value))

    def pick_color():
        color = QColorDialog.getColor(text_color(text), layout.parentWidget())
        if color.isValid():
            text.color = (color.red(), color.green(), color.blue())

    inspector.color.clicked.connect(pick_color)
    inspector.default_color.setToolTip("Use the theme's text color")
    inspector.default_color.clicked.connect(lambda: setattr(text, "color", None))
    color_row = QHBoxLayout()
    color_row.addWidget(inspector.color, stretch=1)
    color_row.addWidget(inspector.default_color)
    layout.addWidget(inspector.edit)
    form = add_form(layout)
    form.addRow("Font color", color_row)
    form.addRow("Font size", inspector.font_size)
    return inspector
