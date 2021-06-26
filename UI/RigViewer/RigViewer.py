from typing import List

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QToolButton, QPushButton
from PySide6.QtCore import Signal, Qt, QTimer
from UI.AppGlobals import AppGlobals
from Model.Rig.RigDevice import RigDevice


class RigViewer(QFrame):
    def __init__(self):
        super().__init__()

        rescanButton = QPushButton("Rescan")
        rescanButton.clicked.connect(self.Rescan)
        self._deviceLayout = QVBoxLayout()
        self._deviceLayout.setContentsMargins(0, 0, 0, 0)
        self._deviceLayout.setSpacing(0)

        self._deviceLayout.addWidget(rescanButton)
        self.setLayout(self._deviceLayout)

        self._deviceItems: List[DeviceItem] = []

        self.UpdateList()

    def Rescan(self):
        AppGlobals.Rig().Rescan()
        self.UpdateList()

    def UpdateList(self):
        for item in self._deviceItems:
            item.deleteLater()
        self._deviceItems = []
        for device in AppGlobals.Rig().savedDevices:
            if device.IsDeviceAvailable() and \
                    device not in [deviceItem.device for deviceItem in self._deviceItems]:
                newItem = DeviceItem(device)
                newItem.numberChanged.connect(self.SortList)
                self._deviceItems.append(newItem)
                self._deviceLayout.addWidget(newItem)

        self.SortList()

    def SortList(self):
        self._deviceItems.sort(key=lambda deviceItem: deviceItem.device.startNumber)
        for item in self._deviceItems:
            self._deviceLayout.removeWidget(item)
        for item in self._deviceItems:
            self._deviceLayout.addWidget(item)


class DeviceItem(QFrame):
    numberChanged = Signal()

    def __init__(self, device: RigDevice):
        super().__init__()

        self.device = device

        self._nameLabel = QLabel(device.serialNumber)
        self._statusLabel = QLabel("")
        self._startNumberDial = QSpinBox()
        self._startNumberDial.setMinimum(0)
        self._startNumberDial.setMaximum(9999)
        self._startNumberDial.setValue(device.startNumber)
        self._startNumberDial.valueChanged.connect(self.SetStartNumber)

        self._enableToggle = QPushButton()
        self._enableToggle.clicked.connect(self.ToggleEnable)
        self._enableToggle.setText("Disable")

        self._layout = QHBoxLayout()
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self.setLayout(self._layout)

        self._layout.addWidget(self._nameLabel, stretch=1)
        self._layout.addWidget(self._statusLabel, stretch=1)
        self._layout.addWidget(self._enableToggle)
        self._layout.addWidget(self._startNumberDial)

        openAllButton = QPushButton("Open All")
        openAllButton.clicked.connect(lambda: self.SetAll(True))
        closeAllButton = QPushButton("Close All")
        closeAllButton.clicked.connect(lambda: self.SetAll(False))

        self._layout.addWidget(openAllButton)
        self._layout.addWidget(closeAllButton)
        self._solenoidButtons: List[SolenoidButton] = []
        for solenoidNumber in range(24):
            newButton = SolenoidButton(solenoidNumber)
            newButton.solenoidClicked.connect(lambda s=newButton: self.ToggleSolenoid(s))
            newButton.polarityClicked.connect(lambda s=newButton: self.TogglePolarity(s))
            self._solenoidButtons.append(newButton)
            self._layout.addWidget(newButton, stretch=0)

        self.Update()

    def SetAll(self, isOpen: bool):
        for i in range(24):
            AppGlobals.Rig().SetSolenoidState(self.device.startNumber + i, isOpen)
        AppGlobals.Rig().FlushStates()

    def SetStartNumber(self):
        self.device.startNumber = self._startNumberDial.value()
        self.Update()
        self.numberChanged.emit()

    def ToggleEnable(self):
        self.device.SetEnabled(not self.device.isEnabled)
        self.Update()

    def ToggleSolenoid(self, button: 'SolenoidButton'):
        index = self._solenoidButtons.index(button)
        AppGlobals.Rig().SetSolenoidState(self.device.startNumber + index,
                                          not AppGlobals.Rig().GetSolenoidState(self.device.startNumber + index))
        AppGlobals.Rig().FlushStates()
        self.Update()

    def TogglePolarity(self, button: 'SolenoidButton'):
        index = self._solenoidButtons.index(button)
        self.device.solenoidPolarities[index] = not self.device.solenoidPolarities[index]
        AppGlobals.Rig().FlushStates()
        self.Update()

    def Update(self):
        if not self.device.IsDeviceAvailable():
            self.deleteLater()
            return

        if self.device.isConnected:
            self._statusLabel.setText("Connected.")
        else:
            if self.device.isEnabled:
                self._statusLabel.setText(self.device.errorMessage)
            else:
                self._statusLabel.setText("Disabled.")

        self._enableToggle.setText({False: "Enable",
                                    True: "Disable"}[self.device.isEnabled])
        self._startNumberDial.setEnabled(self.device.isEnabled and self.device.isConnected)
        for i in range(24):
            self._solenoidButtons[i].setEnabled(self.device.isConnected and self.device.isEnabled)
            self._solenoidButtons[i].Update(self.device.startNumber + i)


class SolenoidButton(QToolButton):
    solenoidClicked = Signal()
    polarityClicked = Signal()

    def __init__(self, number):
        super().__init__()

        self.clicked.connect(self.solenoidClicked.emit)

        self.Update(number)

        timer = QTimer(self)
        timer.timeout.connect(self.UpdateValveState)
        timer.start(30)

        self._number = number
        self._showOpen = None

    def Update(self, number: int):
        self._number = number
        self.setText(str(number))

    def UpdateValveState(self):
        showOpen = AppGlobals.Rig().GetSolenoidState(self._number)
        if showOpen != self._showOpen:
            self.setProperty("IsOpen", showOpen)
            self._showOpen = showOpen
            self.setStyle(self.style())

