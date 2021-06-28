from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QPushButton, QSpinBox, QLabel, QGridLayout, QLineEdit, QVBoxLayout

from UI.ChipEditor.WidgetChipItem import WidgetChipItem, ChipItem
from Model.Valve import Valve
from UI.AppGlobals import AppGlobals


class ValveChipItem(WidgetChipItem):
    def __init__(self, valve: Valve):
        super().__init__()

        AppGlobals.Instance().onChipModified.connect(self.CheckForValve)

        self._valve = valve

        self.valveToggleButton = QPushButton()
        self.valveNumberLabel = QLabel("Number")
        self.valveNumberDial = QSpinBox()
        self.valveNumberDial.setMinimum(0)
        self.valveNumberDial.setValue(self._valve.solenoidNumber)
        self.valveNumberDial.setMaximum(9999)
        self.valveNumberDial.valueChanged.connect(self.UpdateValve)

        self.valveNameLabel = QLabel("Name")
        self.valveNameField = QLineEdit(self._valve.name)
        self.valveNameField.textChanged.connect(self.UpdateValve)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        mainLayout.addWidget(self.valveToggleButton)

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.valveNameLabel, 0, 0)
        layout.addWidget(self.valveNameField, 0, 1)
        layout.addWidget(self.valveNumberLabel, 1, 0)
        layout.addWidget(self.valveNumberDial, 1, 1)

        mainLayout.addLayout(layout)
        self.containerWidget.setLayout(mainLayout)
        self.valveToggleButton.clicked.connect(self.Toggle)

        self._showOpen = None

        self.Update()
        self.Move(QPointF())

    def CheckForValve(self):
        if self._valve not in AppGlobals.Chip().valves:
            self.RemoveItem()

    def Move(self, delta: QPointF):
        if delta != QPointF():
            AppGlobals.Instance().onChipDataModified.emit()
        self._valve.position += delta
        self.GraphicsObject().setPos(self._valve.position)
        super().Move(delta)

    def SetEditDisplay(self, editing: bool):
        self.valveNameField.setVisible(editing)
        self.valveNameLabel.setVisible(editing)
        self.valveNumberLabel.setVisible(editing)
        self.valveNumberDial.setVisible(editing)
        super().SetEditDisplay(editing)

    def UpdateValve(self):
        self._valve.solenoidNumber = self.valveNumberDial.value()
        self._valve.name = self.valveNameField.text()
        AppGlobals.Instance().onChipDataModified.emit()

    def Toggle(self):
        AppGlobals.Rig().SetSolenoidState(self._valve.solenoidNumber,
                                          not AppGlobals.Rig().GetSolenoidState(self._valve.solenoidNumber), True)

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
        text = self._valve.name + "\n(" + str(self._valve.solenoidNumber) + ")"
        if text != self.valveToggleButton.text():
            self.valveToggleButton.setText(text)

        newState = AppGlobals.Rig().GetSolenoidState(self._valve.solenoidNumber)
        if newState != self._showOpen:
            self.valveToggleButton.setProperty("IsOpen", newState)
            self.valveToggleButton.setStyle(self.valveToggleButton.style())
            self._showOpen = newState

        super().Update()
