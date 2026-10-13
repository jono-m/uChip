"""How a valve is shown and edited.

On the canvas (ValveView) it is a button showing the valve's name and solenoid, green when open and red
when closed; clicking it toggles the solenoid. In the inspector (ValveInspector) its name and solenoid
number can be edited.
"""
from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget

from backend.chip import Valve
from backend.rig import Rig
from gui.elements.styles import GREEN, RED, STATE_BUTTON_STYLE
from gui.widgets import add_form, autofit_font, sync_line_edit, sync_spin

OPEN_STYLE = STATE_BUTTON_STYLE.format(*GREEN)
CLOSED_STYLE = STATE_BUTTON_STYLE.format(*RED)


# Canvas

@dataclass(eq=False)
class ValveView:
    valve: Valve
    rig: Rig
    button: QPushButton
    is_open: Optional[bool] = None  # What the button is styled for.

    @property
    def widget(self) -> QWidget:
        return self.button

    def refresh(self):
        text = "%s\n(%d)" % (self.valve.name, self.valve.solenoid)
        if self.button.text() != text:
            self.button.setText(text)
        font = autofit_font(self.button.font(), QSize(self.button.width(), self.button.height() // 2), text)
        if font.pixelSize() != self.button.font().pixelSize():
            self.button.setFont(font)
        is_open = self.rig.get_solenoid(self.valve.solenoid)
        if is_open != self.is_open:
            self.is_open = is_open
            self.button.setStyleSheet(OPEN_STYLE if is_open else CLOSED_STYLE)


def build_valve_view(valve: Valve, rig: Rig) -> ValveView:
    button = QPushButton()
    button.setMinimumSize(1, 1)
    button.clicked.connect(lambda: rig.toggle_solenoid(valve.solenoid))
    return ValveView(valve, rig, button)        


# Inspector

@dataclass(eq=False)
class ValveInspector:
    valve: Valve
    name: QLineEdit
    solenoid: QSpinBox

    def refresh(self):
        sync_line_edit(self.name, self.valve.name)
        sync_spin(self.solenoid, self.valve.solenoid)


def build_valve_inspector(valve: Valve, layout: QVBoxLayout) -> ValveInspector:
    inspector = ValveInspector(valve, QLineEdit(), QSpinBox())
    inspector.solenoid.setRange(0, 1000)
    inspector.name.textEdited.connect(lambda text: setattr(valve, "name", text))
    inspector.solenoid.valueChanged.connect(lambda value: setattr(valve, "solenoid", value))
    form = add_form(layout)
    form.addRow("Name", inspector.name)
    form.addRow("Solenoid", inspector.solenoid)
    return inspector
