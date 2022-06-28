from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QPushButton, QSpinBox, QLabel, QGridLayout, QLineEdit, QHBoxLayout

from UI.ChipEditor.WidgetChipItem import WidgetChipItem, ChipItem
from Model.Valve import Valve
from UI.AppGlobals import AppGlobals


class ValveChipItem(WidgetChipItem):
    def __init__(self, valve: Valve):
        super().__init__()

        AppGlobals.Instance().onChipAddRemove.connect(self.CheckForValve)
        AppGlobals.Instance().onValveChanged.connect(self.UpdateDisplay)

        self._valve = valve

        self.valveToggleButton = QPushButton()
        self.valveToggleButton.setObjectName("ValveButton")
        self.containerWidget.setObjectName("ValveContainer")
        self.valveNumberLabel = QLabel("Number")
        self.valveNumberDial = QSpinBox()
        self.valveNumberDial.setMinimum(0)
        self.valveNumberDial.setValue(self._valve.solenoidNumber)
        self.valveNumberDial.setMaximum(9999)
        self.valveNumberDial.valueChanged.connect(self.UpdateValve)

        self.valveNameLabel = QLabel("Name")
        self.valveNameField = QLineEdit(self._valve.name)
        self.valveNameField.textChanged.connect(self.UpdateValve)

        mainLayout = QHBoxLayout()
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
        self.HoverWidget().setLayout(layout)

        self.containerWidget.setLayout(mainLayout)
        self.valveToggleButton.clicked.connect(self.Toggle)

        self._showOpen = None

        self.UpdateDisplay()
        self.Move(QPointF())

    def SetEditing(self, isEditing: bool):
        self.valveToggleButton.blockSignals(isEditing)

    def CheckForValve(self):
        if self._valve not in AppGlobals.Chip().valves:
            self.RemoveItem()

    def Move(self, delta: QPointF):
        if delta != QPointF():
            AppGlobals.Instance().onChipDataModified.emit()
        self._valve.position += delta
        self.GraphicsObject().setPos(self._valve.position)
        super().Move(delta)

    def UpdateValve(self):
        self._valve.solenoidNumber = self.valveNumberDial.value()
        self._valve.name = self.valveNameField.text()
        AppGlobals.Instance().onChipDataModified.emit()
        self.UpdateDisplay()

    def Toggle(self):
        AppGlobals.Rig().SetSolenoidState(self._valve.solenoidNumber,
                                          not AppGlobals.Rig().GetSolenoidState(self._valve.solenoidNumber), True)
        AppGlobals.Instance().onValveChanged.emit()

    def RequestDelete(self):
        AppGlobals.Chip().valves.remove(self._valve)
        AppGlobals.Instance().onChipAddRemove.emit()

    def Duplicate(self) -> 'ChipItem':
        newValve = Valve()
        newValve.position = QPointF(self._valve.position)
        newValve.name = self._valve.name
        newValve.solenoidNumber = AppGlobals.Chip().NextSolenoidNumber()

        AppGlobals.Chip().valves.append(newValve)
        AppGlobals.Instance().onChipAddRemove.emit()
        return ValveChipItem(newValve)

    def UpdateDisplay(self):
        text = self._valve.name + "\n(" + str(self._valve.solenoidNumber) + ")"
        if text != self.valveToggleButton.text():
            self.valveToggleButton.setText(text)

        newState = AppGlobals.Rig().GetSolenoidState(self._valve.solenoidNumber)
        if newState != self._showOpen:
            self.valveToggleButton.setProperty("On", newState)
            self.valveToggleButton.setProperty("Off", not newState)
            self.valveToggleButton.setStyle(self.valveToggleButton.style())
            self._showOpen = newState
