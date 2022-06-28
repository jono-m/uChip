from typing import List, Tuple, Optional

from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QFrame, QHBoxLayout, QListWidgetItem, \
    QMessageBox, QLabel, QCheckBox, QSpinBox, QWidget
from PySide6.QtGui import QValidator
from UI.AppGlobals import AppGlobals
from Model.Rig.RigDevice import RigDevice


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
