from typing import List

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, QPushButton, QSizePolicy
from PySide6.QtCore import Signal, Qt
from UI.AppGlobals import AppGlobals
from Data.Rig.RigDevice import RigDevice
from UI.RigViewer.RigSettingsWidget import RigSettingsWidget


class RigView(QFrame):
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
        mainLayout.addWidget(self._devicesListWidget, stretch=0)
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
            self._solenoidButtons.append(newButton)
            self.solenoidsLayout.addWidget(newButton, stretch=0)

        self.setLayout(self.solenoidsLayout)

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

from typing import List, Tuple, Optional

from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QFrame, QHBoxLayout, QListWidgetItem, \
    QMessageBox, QLabel, QCheckBox, QSpinBox, QWidget
from PySide6.QtGui import QValidator
from UI.AppGlobals import AppGlobals
from Data.Rig.RigDevice import RigDevice


class RigSettingsWidget(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setModal(True)

        self.setWindowTitle("Device Configuration")

        self.availableDevicesList = QListWidget()
        self.availableDevicesList.currentItemChanged.connect(self.OnListItemChanged)

        self.deviceInfoWidget = DeviceInfoWidget()

        mainLayout = QVBoxLayout()
        midLayout = QHBoxLayout()
        midLayout.addWidget(self.availableDevicesList)
        midLayout.addWidget(self.deviceInfoWidget)
        mainLayout.addLayout(midLayout)
        self.setLayout(mainLayout)

        AppGlobals.Instance().onDevicesChanged.connect(self.RepopulateList)

        self._itemDeviceMapping: List[Tuple[QListWidgetItem, RigDevice]] = []

        self.RepopulateList()

    def DeviceForItem(self, item: QListWidgetItem):
        if item is None:
            return None
        device = [device for (i, device) in self._itemDeviceMapping if i == item]
        if len(device) > 0:
            return device[0]
        return None

    def OnListItemChanged(self, currentItem, previousItem):
        device = self.DeviceForItem(currentItem)
        if self.PromptSwitchDevice(device):
            self.deviceInfoWidget.DisplayInfoForDevice(device)
        else:
            lastIndex = self.availableDevicesList.indexFromItem(previousItem)
            self.availableDevicesList.blockSignals(True)
            self.availableDevicesList.setCurrentIndex(lastIndex)
            self.availableDevicesList.blockSignals(False)

    def closeEvent(self, arg__1) -> None:
        if not self.PromptSwitchDevice(None):
            arg__1.ignore()
        else:
            super().closeEvent(arg__1)

    def RepopulateList(self):
        self.availableDevicesList.blockSignals(True)

        currentDevice = self.deviceInfoWidget.Device()
        self.availableDevicesList.clear()
        self._itemDeviceMapping.clear()
        currentItem = None
        for device in AppGlobals.Rig().GetAvailableDevices():
            newItem = QListWidgetItem(device.Name())
            self._itemDeviceMapping.append((newItem, device))
            if device == currentDevice:
                currentItem = newItem
            self.availableDevicesList.addItem(newItem)

        self.availableDevicesList.blockSignals(False)

        if currentItem:
            self.availableDevicesList.setCurrentItem(currentItem)
        elif self.availableDevicesList.count() > 0:
            self.availableDevicesList.setCurrentRow(0)

    # Return true if the switch was accepted
    def PromptSwitchDevice(self, device: Optional[RigDevice]) -> bool:
        if self.deviceInfoWidget.Device() != device and self.deviceInfoWidget.IsModified():
            ret = QMessageBox.question(self, "Confirm Change",
                                       "You have unsaved changes to this device. Do you want to discard them?",
                                       QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                                       QMessageBox.Save)

            if ret == QMessageBox.Save:
                self.deviceInfoWidget.Save()
            elif ret == QMessageBox.Cancel:
                return False
        return True


class DeviceInfoWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.saveButton = QPushButton("Save")
        self.saveButton.clicked.connect(self.Save)

        self.nameLabel = QLabel("")
        self.descriptionLabel = QLabel("")

        self.enabledCheckbox = QCheckBox("Enabled")
        self.enabledCheckbox.stateChanged.connect(self._Modified)

        self.invertedACheckbox = QCheckBox("Invert Solenoids 0-7")
        self.invertedACheckbox.stateChanged.connect(self._Modified)

        self.invertedBCheckbox = QCheckBox("Invert Solenoids 8-15")
        self.invertedBCheckbox.stateChanged.connect(self._Modified)

        self.invertedCCheckbox = QCheckBox("Invert Solenoids 16-23")
        self.invertedCCheckbox.stateChanged.connect(self._Modified)

        self.startNumber = QSpinBox()
        self.startNumber.setCorrectionMode(QSpinBox.CorrectToNearestValue)
        self.startNumber.validate = self.ValidateNumber
        self.startNumber.setMinimum(0)
        self.startNumber.setMaximum(9999)
        self.startNumber.setSingleStep(24)
        self.startNumber.valueChanged.connect(self._Modified)

        startNumberLayout = QHBoxLayout()
        startNumberLayout.addWidget(QLabel("Start Number: "))
        startNumberLayout.addWidget(self.startNumber)

        layout = QVBoxLayout()
        layout.addWidget(self.nameLabel)
        layout.addWidget(self.descriptionLabel)
        layout.addWidget(self.enabledCheckbox)
        layout.addWidget(self.invertedACheckbox)
        layout.addWidget(self.invertedBCheckbox)
        layout.addWidget(self.invertedCCheckbox)
        layout.addLayout(startNumberLayout)
        layout.addWidget(self.saveButton)
        layout.addStretch(1)
        self.setLayout(layout)

        self._currentDevice = None
        self._modified = False

    def ValidateNumber(self, number: str, pos):
        if not number.isnumeric():
            return QValidator.Invalid
        number = int(float(number))
        if number % 24 == 0:
            return QValidator.Acceptable
        else:
            return QValidator.Intermediate

    def IsModified(self):
        return self._modified

    def Device(self):
        return self._currentDevice

    def DisplayInfoForDevice(self, device: RigDevice):
        self._currentDevice = device

        if self._currentDevice is None:
            [t.setVisible(False) for t in self.children() if isinstance(t, QWidget)]
            self.nameLabel.setVisible(True)
            self.nameLabel.setText("No device selected.")
        else:
            [t.setVisible(True) for t in self.children() if isinstance(t, QWidget)]
            self.nameLabel.setText("Name: %s" % self._currentDevice.livePortInfo.name)
            self.descriptionLabel.setText(("Port: %s\n"
                                           "Serial Number: %s\n"
                                           "Description: %s\n") % (self._currentDevice.livePortInfo.device,
                                                                   self._currentDevice.livePortInfo.serial_number,
                                                                   self._currentDevice.livePortInfo.description))

            self.invertedACheckbox.setChecked(self._currentDevice.polarities[0])
            self.invertedBCheckbox.setChecked(self._currentDevice.polarities[1])
            self.invertedCCheckbox.setChecked(self._currentDevice.polarities[2])

            self.enabledCheckbox.setChecked(self._currentDevice.enabled)

            self.startNumber.setValue(self._currentDevice.startNumber)

        self.saveButton.setEnabled(False)
        self._modified = False

    def Save(self):
        self._currentDevice.enabled = self.enabledCheckbox.isChecked()
        self._currentDevice.polarities[0] = self.invertedACheckbox.isChecked()
        self._currentDevice.polarities[1] = self.invertedBCheckbox.isChecked()
        self._currentDevice.polarities[2] = self.invertedCCheckbox.isChecked()
        self._currentDevice.startNumber = self.startNumber.value()
        self._modified = False
        self.saveButton.setEnabled(False)
        try:
            AppGlobals.UpdateRig(True)
        except Exception as e:
            QMessageBox.critical(self, "Rig Device Error!", str(e))

    def _Modified(self):
        self._modified = True
        self.saveButton.setEnabled(True)
