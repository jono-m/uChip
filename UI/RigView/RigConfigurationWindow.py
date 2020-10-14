from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from Rig.Rig import Rig
from Rig.Device import Device
from UI.STYLESHEET import *
import typing


class RigConfigurationWindow(QDialog):
    def __init__(self, rig: Rig, *args, **kwargs):
        super().__init__(f=Qt.WindowTitleHint | Qt.WindowCloseButtonHint, *args, **kwargs)

        self.setModal(True)
        self.rig = rig

        self.rig.ReconnectAll()

        self.listDisplay = QListWidget()
        self.listDisplay.itemSelectionChanged.connect(self.OnSelectionChanged)
        self.listDisplay.setStyleSheet(stylesheet)

        upButton = QPushButton("Move Up \u25B2")
        downButton = QPushButton("Move Down \u25BC")
        upButton.clicked.connect(self.MoveUp)
        downButton.clicked.connect(self.MoveDown)

        self.serialNumberDisplay = QLabel("Device name")
        self.invertOne = QCheckBox("Invert panel 1 power")
        self.invertOne.stateChanged.connect(self.OnInversionChanged)
        self.invertTwo = QCheckBox("Invert panel 2 power")
        self.invertTwo.stateChanged.connect(self.OnInversionChanged)
        self.invertThree = QCheckBox("Invert panel 3 power")
        self.invertThree.stateChanged.connect(self.OnInversionChanged)

        settingsPanel = QFrame()
        settingsLayout = QVBoxLayout()
        settingsLayout.addWidget(self.serialNumberDisplay)
        settingsLayout.addWidget(self.invertOne)
        settingsLayout.addWidget(self.invertTwo)
        settingsLayout.addWidget(self.invertThree)
        settingsPanel.setLayout(settingsLayout)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(upButton)
        buttonsLayout.addWidget(downButton)

        listLayout = QVBoxLayout()
        listLayout.addWidget(self.listDisplay)
        listLayout.addLayout(buttonsLayout)

        layout = QVBoxLayout()

        mainLayout = QHBoxLayout()

        layout.addLayout(mainLayout)

        mainLayout.addLayout(listLayout)
        mainLayout.addLayout(buttonsLayout)
        mainLayout.addWidget(settingsPanel)

        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        layout.addWidget(ok)

        self.setLayout(layout)
        self.setWindowTitle("Rig configuration")

        # Remember the selected serial number during ordering changes etc
        self.selectedDeviceSerialNumber = ""

        self.RefreshDeviceList()
        self.show()

    # Repopulate the list of devices and select the remembered serial number if it exists
    def RefreshDeviceList(self):
        self.listDisplay.blockSignals(True)
        self.listDisplay.clear()

        indexToSelect = -1
        for deviceIndex in range(len(self.rig.GetConnectedDevices())):
            device = self.rig.GetConnectedDevices()[deviceIndex]
            if device.portInfo.serial_number == self.selectedDeviceSerialNumber:
                indexToSelect = deviceIndex
            QListWidgetItem(device.portInfo.serial_number, self.listDisplay)

        self.listDisplay.blockSignals(False)

        # Select the previously selected device
        if indexToSelect == -1:
            # No matching devices from last selection found
            if self.listDisplay.count() > 0:
                self.listDisplay.item(0).setSelected(True)
        else:
            self.listDisplay.item(indexToSelect).setSelected(True)
        self.OnSelectionChanged()

    def CurrentSelectedDevice(self) -> typing.Optional[Device]:
        if len(self.listDisplay.selectedItems()) == 0:
            return None
        else:
            return self.rig.GetConnectedDevices()[self.listDisplay.selectedIndexes()[0].row()]

    # Whenever the selection was changed, either through refreshing the list of devices, or clicking on a new item
    def OnSelectionChanged(self):
        currentDevice = self.CurrentSelectedDevice()

        if currentDevice is None:
            self.selectedDeviceSerialNumber = ""
            self.serialNumberDisplay.setText("No device selected.")
            self.invertOne.hide()
            self.invertTwo.hide()
            self.invertThree.hide()
            return

        # Save the selected serial number, in case we reorder things
        self.selectedDeviceSerialNumber = currentDevice.portInfo.serial_number

        self.invertOne.blockSignals(True)
        self.invertTwo.blockSignals(True)
        self.invertThree.blockSignals(True)

        self.serialNumberDisplay.setText(currentDevice.portInfo.serial_number)
        (invertOne, invertTwo, invertThree) = self.rig.GetDeviceInversion(currentDevice.portInfo.serial_number)
        self.invertOne.setChecked(invertOne)
        self.invertTwo.setChecked(invertTwo)
        self.invertThree.setChecked(invertThree)

        self.invertOne.show()
        self.invertTwo.show()
        self.invertThree.show()

        self.invertOne.blockSignals(False)
        self.invertTwo.blockSignals(False)
        self.invertThree.blockSignals(False)

    def OnInversionChanged(self):
        # Update the inversion settings for the current device.
        currentDevice = self.CurrentSelectedDevice()
        self.rig.SetDeviceInversion(currentDevice.portInfo.serial_number, self.invertOne.isChecked(),
                                    self.invertTwo.isChecked(),
                                    self.invertThree.isChecked())

    def MoveUp(self):
        self.rig.Demote(self.CurrentSelectedDevice())
        self.RefreshDeviceList()

    def MoveDown(self):
        self.rig.Promote(self.CurrentSelectedDevice())
        self.RefreshDeviceList()
