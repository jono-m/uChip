import PySide6.QtGui

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QToolButton, QVBoxLayout, QSpinBox, QLabel, QHBoxLayout

from UI.ChipEditor.WidgetChipItem import WidgetChipItem, Chip, ChipItem
from Model.Valve import Valve, ValveState


class ValveChipItem(WidgetChipItem):
    def __init__(self, chip: Chip, valve: Valve):
        super().__init__(chip)

        self._valve = valve

        self.valveToggleButton = QToolButton()
        layout = QVBoxLayout()
        layout.addWidget(self.valveToggleButton)
        self.containerWidget.setLayout(layout)
        self.containerWidget.adjustSize()
        self.valveToggleButton.clicked.connect(self._valve.Toggle)

        self.Update()
        self.Move(QPointF())

    def Move(self, delta: QPointF):
        self._valve.position += delta
        self.GraphicsObject().setPos(self._valve.position)

    def Delete(self):
        super().Delete()
        self.Chip().valves.remove(self._valve)

    def Duplicate(self) -> 'ChipItem':
        newValve = Valve()
        newValve.position = QPointF(self._valve.position)
        newValve.name = self._valve.name
        newValve.solenoidNumber = self.Chip().NextSolenoidNumber()

        self.Chip().valves.append(newValve)
        return ValveChipItem(self.Chip(), newValve)

    def Update(self):
        self.valveToggleButton.setText(str(self._valve.name))
        lastState = self.valveToggleButton.property("valveState")
        newState = {ValveState.OPEN: "OPEN",
                    ValveState.CLOSED: "CLOSED"}[self._valve.state]
        if lastState != newState:
            self.valveToggleButton.setProperty("valveState", newState)
            self.valveToggleButton.setStyle(self.valveToggleButton.style())
