from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QToolButton, QVBoxLayout, QSpinBox, QLabel

from UI.ChipEditor.WidgetChipItem import WidgetChipItem, Chip, ChipItem
from Model.Valve import Valve
from UI.AppGlobals import AppGlobals


class ValveChipItem(WidgetChipItem):
    def __init__(self, valve: Valve):
        super().__init__()

        self._valve = valve

        self.valveToggleButton = QToolButton()
        self.valveNumberLabel = QLabel("Solenoid Number")
        self.valveNumberDial = QSpinBox()
        self.valveNumberDial.setMinimum(0)
        self.valveNumberDial.setMaximum(9999)
        self.valveNumberDial.valueChanged.connect(self.UpdateNumber)

        layout = QVBoxLayout()
        layout.addWidget(self.valveToggleButton)
        layout.addWidget(self.valveNumberLabel)
        layout.addWidget(self.valveNumberDial)
        self.containerWidget.setLayout(layout)
        self.containerWidget.adjustSize()
        self.valveToggleButton.clicked.connect(self.Toggle)

        self.Update()
        self.Move(QPointF())

    def Move(self, delta: QPointF):
        self._valve.position += delta
        self.GraphicsObject().setPos(self._valve.position)

    def UpdateNumber(self):
        self._valve.solenoidNumber = self.valveNumberDial.value()

    def Toggle(self):
        AppGlobals.Rig().SetSolenoidState(self._valve.solenoidNumber,
                                          not AppGlobals.Rig().GetSolenoidState(self._valve.solenoidNumber))

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
        newState = {True: "OPEN",
                    False: "CLOSED"}[AppGlobals.Rig().GetSolenoidState(self._valve.solenoidNumber)]
        if lastState != newState:
            self.valveToggleButton.setProperty("valveState", newState)
            self.valveToggleButton.setStyle(self.valveToggleButton.style())
