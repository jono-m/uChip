from typing import List

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QToolButton, QPushButton, QGridLayout, \
    QSizePolicy
from PySide6.QtCore import Signal, Qt, QTimer, QObject
from UI.AppGlobals import AppGlobals
from Model.Rig.RigDevice import RigDevice


class RigViewer(QFrame):
    def __init__(self):
        super().__init__()

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        mainLayout.setAlignment(Qt.AlignTop)
        self.setLayout(mainLayout)

        rescanButton = QPushButton("Rescan")
        rescanButton.setProperty("Attention", True)
        rescanButton.clicked.connect(self.Rescan)
        rescanButton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self._deviceLayout = QGridLayout()
        self._deviceLayout.setAlignment(Qt.AlignTop)
        self._deviceLayout.setContentsMargins(0, 0, 0, 0)
        self._deviceLayout.setSpacing(0)

        self._deviceLayout.addWidget(QLabel("Device Name"), 0, 0)
        self._deviceLayout.addWidget(QLabel("Status"), 0, 1)
        self._deviceLayout.addWidget(QLabel("Start Number"), 0, 2)
        solenoidLayout = QHBoxLayout()
        solenoidLayout.addWidget(QLabel("Solenoids"))
        solenoidLayout.addWidget(rescanButton, stretch=0)
        self._deviceLayout.addLayout(solenoidLayout, 0, 3)
        mainLayout.addLayout(self._deviceLayout, stretch=0)
        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

        even = False
        for item in self.children():
            item.setProperty("IsHeader", True)
            item.setProperty("IsColumnEven", even)
            even = not even
            if isinstance(item, QLabel):
                item.setAlignment(Qt.AlignCenter)

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

        self.SortList()

    def SortList(self):
        self._deviceItems.sort(key=lambda deviceItem: deviceItem.device.startNumber)
        self.FillList()

    def FillList(self):
        for row in range(1, self._deviceLayout.rowCount()):
            [self._deviceLayout.removeItem(self._deviceLayout.itemAtPosition(row, column)) for column in range(4)]
        for row, item in enumerate(self._deviceItems):
            self._deviceLayout.addWidget(item.nameLabel, row + 1, 0)
            self._deviceLayout.addLayout(item.statusLayout, row + 1, 1)
            self._deviceLayout.addWidget(item.startNumberDial, row + 1, 2)
            self._deviceLayout.addLayout(item.solenoidsLayout, row + 1, 3)


class DeviceItem(QObject):
    numberChanged = Signal()

    def __init__(self, device: RigDevice):
        super().__init__()

        self.device = device

        self.nameLabel = QLabel(device.serialNumber)
        self.nameLabel.setAlignment(Qt.AlignCenter)
        self._statusLabel = QLabel("")
        self._statusLabel.setAlignment(Qt.AlignCenter)
        self.startNumberDial = QSpinBox()
        self.startNumberDial.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.startNumberDial.setMinimum(0)
        self.startNumberDial.setMaximum(9999)
        self.startNumberDial.setValue(device.startNumber)
        self.startNumberDial.valueChanged.connect(self.SetStartNumber)

        self._enableToggle = QPushButton()
        self._enableToggle.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self._enableToggle.clicked.connect(self.ToggleEnable)
        self._enableToggle.setText("Disable")

        self.openAllButton = QPushButton("Open All")
        self.openAllButton.clicked.connect(lambda: self.SetAll(True))
        self.openAllButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.closeAllButton = QPushButton("Close All")
        self.closeAllButton.clicked.connect(lambda: self.SetAll(False))
        self.closeAllButton.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.statusLayout = QHBoxLayout()
        self.statusLayout.addWidget(self._statusLabel, stretch=1)
        self.statusLayout.addWidget(self._enableToggle, stretch=0)

        self.solenoidsLayout = QHBoxLayout()
        openCloseLayout = QVBoxLayout()
        openCloseLayout.addWidget(self.openAllButton)
        openCloseLayout.addWidget(self.closeAllButton)
        self.solenoidsLayout.addLayout(openCloseLayout)
        self._solenoidButtons: List[SolenoidButton] = []
        for solenoidNumber in range(24):
            newButton = SolenoidButton(solenoidNumber)
            newButton.solenoidClicked.connect(lambda s=newButton: self.ToggleSolenoid(s))
            newButton.polarityClicked.connect(lambda s=newButton: self.TogglePolarity(s))
            self._solenoidButtons.append(newButton)
            self.solenoidsLayout.addWidget(newButton, stretch=0)

        self.Update()

    def SetAll(self, isOpen: bool):
        for i in range(24):
            AppGlobals.Rig().SetSolenoidState(self.device.startNumber + i, isOpen)
        AppGlobals.Rig().FlushStates()

    def SetStartNumber(self):
        self.device.startNumber = self.startNumberDial.value()
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
        self.startNumberDial.setEnabled(self.device.isEnabled and self.device.isConnected)
        self.openAllButton.setEnabled(self.device.isEnabled and self.device.isConnected)
        self.closeAllButton.setEnabled(self.device.isEnabled and self.device.isConnected)
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
