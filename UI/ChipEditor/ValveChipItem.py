from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QToolButton, QSpinBox, QLabel, QGridLayout, QLineEdit

from UI.ChipEditor.WidgetChipItem import WidgetChipItem, ChipItem
from Model.Valve import Valve
from UI.AppGlobals import AppGlobals


class ValveChipItem(WidgetChipItem):
    def __init__(self, valve: Valve):
        super().__init__()

        AppGlobals.Instance().onChipModified.connect(self.CheckForValve)

        self._valve = valve

        self.valveToggleButton = QToolButton()
        self.valveNumberLabel = QLabel("Number")
        self.valveNumberDial = QSpinBox()
        self.valveNumberDial.setMinimum(0)
        self.valveNumberDial.setMaximum(9999)
        self.valveNumberDial.valueChanged.connect(self.UpdateValve)

        self.valveNameLabel = QLabel("Name")
        self.valveNameField = QLineEdit()
        self.valveNameField.textChanged.connect(self.UpdateValve)

        layout = QGridLayout()
        layout.addWidget(self.valveToggleButton, 0, 0, 1, 2)
        layout.addWidget(self.valveNameLabel, 1, 0)
        layout.addWidget(self.valveNameField, 1, 1)
        layout.addWidget(self.valveNumberLabel, 2, 0)
        layout.addWidget(self.valveNumberDial, 2, 1)
        self.containerWidget.setLayout(layout)
        self.containerWidget.adjustSize()
        self.valveToggleButton.clicked.connect(self.Toggle)

        self.Update()
        self.Move(QPointF())

    def CheckForValve(self):
        if self._valve not in AppGlobals.Chip().valves:
            self.RemoveItem()

    def Move(self, delta: QPointF):
        self._valve.position += delta
        self.GraphicsObject().setPos(self._valve.position)

    def SetEditDisplay(self, editing: bool):
        self.valveNameField.setVisible(editing)
        self.valveNameLabel.setVisible(editing)
        self.valveNumberLabel.setVisible(editing)
        self.valveNumberDial.setVisible(editing)
        self.containerWidget.adjustSize()

    def UpdateValve(self):
        self._valve.solenoidNumber = self.valveNumberDial.value()
        self._valve.name = self.valveNameField.text()

    def Toggle(self):
        AppGlobals.Rig().SetSolenoidState(self._valve.solenoidNumber,
                                          not AppGlobals.Rig().GetSolenoidState(self._valve.solenoidNumber))

    def RequestDelete(self):
        AppGlobals.Chip().valves.remove(self._valve)
        AppGlobals.Instance().onChipModified.emit()

    def Duplicate(self) -> 'ChipItem':
        newValve = Valve()
        newValve.position = QPointF(self._valve.position)
        newValve.name = self._valve.name
        newValve.solenoidNumber = AppGlobals.Chip().NextSolenoidNumber()

        AppGlobals.Chip().valves.append(newValve)
        AppGlobals.Instance().onChipModified.emit()
        return ValveChipItem(newValve)

    def Update(self):
        text = self._valve.name + " (" + str(self._valve.solenoidNumber) + ")"
        if text != self.valveToggleButton.text():
            self.valveToggleButton.setText(text)

        if self._valve.name != self.valveNameField.text():
            self.valveNameField.setText(self._valve.name)

        lastState = self.valveToggleButton.property("valveState")
        newState = {True: "OPEN",
                    False: "CLOSED"}[AppGlobals.Rig().GetSolenoidState(self._valve.solenoidNumber)]
        if lastState != newState:
            self.valveToggleButton.setProperty("valveState", newState)
            self.valveToggleButton.setStyle(self.valveToggleButton.style())
