from typing import List

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, QPushButton, QSizePolicy
from PySide6.QtCore import Signal, Qt
from UI.AppGlobals import AppGlobals
from Model.Rig.RigDevice import RigDevice
from UI.RigViewer.RigSettingsWidget import RigSettingsWidget


class RigViewer(QFrame):
    def __init__(self):
        super().__init__()

        self._headerWidget = QFrame()
        headerLayout = QHBoxLayout()
        self._headerWidget.setLayout(headerLayout)
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.setSpacing(0)
        self._rigStatusLabel = QLabel()
        headerLayout.addWidget(self._rigStatusLabel, stretch=1)
        settingsButton = QPushButton("Configure devices...")
        settingsButton.clicked.connect(self.OpenSettings)
        headerLayout.addWidget(settingsButton, stretch=0)

        self._devicesListWidget = QFrame()
        self._deviceLayout = QVBoxLayout()
        self._deviceLayout.setAlignment(Qt.AlignTop)
        self._deviceLayout.setContentsMargins(0, 0, 0, 0)
        self._deviceLayout.setSpacing(0)
        self._devicesListWidget.setLayout(self._deviceLayout)

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        mainLayout.setAlignment(Qt.AlignTop)
        mainLayout.addWidget(self._headerWidget, stretch=0)
        mainLayout.addWidget(self._devicesListWidget, stretch=1)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

        self._deviceItems: List[DeviceItem] = []

        AppGlobals.Instance().onDevicesChanged.connect(self.UpdateList)

        self.UpdateList()

    def UpdateList(self):
        for item in self._deviceItems:
            item.deleteLater()
        self._deviceItems = []
        devices = AppGlobals.Rig().GetActiveDevices()
        devices.sort(key=lambda x: x.startNumber)
        for device in devices:
            if device.enabled and device not in [deviceItem.device for deviceItem in self._deviceItems]:
                newItem = DeviceItem(device)
                self._deviceItems.append(newItem)
                self._deviceLayout.addWidget(newItem)

        if len(self._deviceItems) == 0:
            self._rigStatusLabel.setText("<i>No configured devices found.</i>")
        else:
            self._rigStatusLabel.setText("<i>Connected to %d devices.</i>" % len(self._deviceItems))

    def OpenSettings(self):
        settingsWindow = RigSettingsWidget(self)
        settingsWindow.exec()


class DeviceItem(QFrame):
    def __init__(self, device: RigDevice):
        super().__init__()

        self.device = device

        self.openAllButton = QPushButton("All On")
        self.openAllButton.clicked.connect(lambda: self.SetAll(True))
        self.openAllButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.closeAllButton = QPushButton("All Off")
        self.closeAllButton.clicked.connect(lambda: self.SetAll(False))
        self.closeAllButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.solenoidsLayout = QHBoxLayout()
        openCloseLayout = QHBoxLayout()
        openCloseLayout.addWidget(self.openAllButton)
        openCloseLayout.addWidget(self.closeAllButton)
        self.solenoidsLayout.addLayout(openCloseLayout)
        self._solenoidButtons: List[SolenoidButton] = []
        for solenoidNumber in range(24):
            newButton = SolenoidButton(solenoidNumber + self.device.startNumber)
            newButton.solenoidClicked.connect(lambda s=newButton: self.ToggleSolenoid(s))
            newButton.polarityClicked.connect(lambda s=newButton: self.TogglePolarity(s))
            self._solenoidButtons.append(newButton)
            self.solenoidsLayout.addWidget(newButton, stretch=0)

        self.setLayout(self.solenoidsLayout)
        self.Update()

    def SetAll(self, isOpen: bool):
        for i in range(24):
            AppGlobals.Rig().SetSolenoidState(self.device.startNumber + i, isOpen)
        AppGlobals.Rig().FlushStates()
        AppGlobals.Instance().onValveChanged.emit()

    def ToggleSolenoid(self, button: 'SolenoidButton'):
        index = self._solenoidButtons.index(button)
        AppGlobals.Rig().SetSolenoidState(self.device.startNumber + index,
                                          not AppGlobals.Rig().GetSolenoidState(self.device.startNumber + index), True)
        AppGlobals.Instance().onValveChanged.emit()


class SolenoidButton(QToolButton):
    solenoidClicked = Signal()
    polarityClicked = Signal()

    def __init__(self, number):
        super().__init__()

        self.clicked.connect(self.solenoidClicked.emit)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        AppGlobals.Instance().onValveChanged.connect(self.UpdateValveState)

        self.Update(number)

        self._number = number
        self._showOpen = None
        self.UpdateValveState()

    def Update(self, number: int):
        self._number = number
        self.setText(str(number))

    def UpdateValveState(self):
        showOpen = AppGlobals.Rig().GetSolenoidState(self._number)
        if showOpen != self._showOpen:
            self.setProperty("On", showOpen)
            self._showOpen = showOpen
            self.setStyle(self.style())
