from UI.RigView.RigConfigurationWindow import *
from Util import *


class RigViewWidget(QDialog):
    def __init__(self, rig: Rig, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowFlags(Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)

        self.setWindowTitle("Rig Solenoids")

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.setLayout(self.mainLayout)

        self.solenoidButtons: typing.List[SolenoidButton] = []

        buttonLayout = QHBoxLayout()
        buttonLayout.setAlignment(Qt.AlignLeft)
        configureButton = QPushButton()
        configureButton.setText("Configure Rig...")
        configureButton.clicked.connect(self.ShowDialog)

        closeButton = QPushButton("Close")
        closeButton.clicked.connect(lambda: self.accept())
        buttonLayout.addWidget(configureButton, stretch=0)
        buttonLayout.addWidget(QLabel(), stretch=1)
        buttonLayout.addWidget(closeButton, stretch=0)

        self.solenoidsScrollArea = QScrollArea()

        self.mainLayout.addWidget(self.solenoidsScrollArea)
        self.mainLayout.addLayout(buttonLayout)

        self.solenoidsContainer = QFrame()

        self.solenoidsScrollArea.setWidget(self.solenoidsContainer)
        self.solenoidsScrollArea.setWidgetResizable(True)

        self.solenoidsLayout = QVBoxLayout()
        self.solenoidsLayout.setContentsMargins(0, 0, 0, 0)
        self.solenoidsLayout.setSpacing(0)

        self.solenoidsContainer.setLayout(self.solenoidsLayout)

        self.rig = rig

        self.rig.OnFlush.Register(self.UpdateDisplay)

        self.Repopulate()
        self.setModal(True)

    def ShowDialog(self):
        newWindow = RigConfigurationWindow(self.rig, parent=self)
        newWindow.finished.connect(self.Repopulate)
        newWindow.exec_()

    def Repopulate(self):
        for i in reversed(range(self.solenoidsLayout.count())):
            self.solenoidsLayout.itemAt(i).widget().deleteLater()

        self.solenoidButtons = []

        currentLayout = None
        for solenoidNumber in range(len(self.rig.solenoidStates)):
            row = int(solenoidNumber / 8)
            column = solenoidNumber % 8

            if column == 0:
                container = QFrame()
                currentLayout = QHBoxLayout()
                currentLayout.setContentsMargins(0, 0, 0, 0)
                currentLayout.setSpacing(0)
                container.setLayout(currentLayout)
                container.setProperty("IsEven", row % 2 == 0)
                self.solenoidsLayout.addWidget(container)

                eightSet = range(row * 8, (row + 1) * 8)
                onButton = QPushButton("OPEN ALL")
                onButton.clicked.connect(
                    lambda checked=False, es=eightSet: self.EightSetButtonPressed(es, True))
                offButton = QPushButton("CLOSE ALL")
                offButton.clicked.connect(
                    lambda checked=False, es=eightSet: self.EightSetButtonPressed(es, False))
                currentLayout.addWidget(onButton)
                currentLayout.addWidget(offButton)

            newSolenoidButton = SolenoidButton(text=str(solenoidNumber))
            newSolenoidButton.clicked.connect(
                lambda checked=False, num=solenoidNumber: self.SolenoidClickedHandler(num))
            self.solenoidButtons.append(newSolenoidButton)

            currentLayout.addWidget(newSolenoidButton)

        if len(self.solenoidButtons) == 0:
            self.solenoidsLayout.addWidget(QLabel("No devices connected."), 0, 0)

        self.adjustSize()

    def EightSetButtonPressed(self, eightSet, isOn):
        for solenoidNumber in eightSet:
            if solenoidNumber not in self.rig.drivenSolenoids:
                self.rig.SetSolenoid(solenoidNumber, isOn)
        self.rig.Flush()

    def SolenoidClickedHandler(self, number):
        self.rig.SetSolenoid(number, not self.rig.IsSolenoidOn(number))
        self.rig.Flush()

    def UpdateDisplay(self):
        for i in range(len(self.solenoidButtons)):
            self.solenoidButtons[i].setEnabled(i not in self.rig.drivenSolenoids)
            self.solenoidButtons[i].setChecked(self.rig.IsSolenoidOn(i))
            if self.solenoidButtons[i].isEnabled():
                self.solenoidButtons[i].setToolTip("")
            else:
                self.solenoidButtons[i].setToolTip("Driven by chip.")


class SolenoidButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCheckable(True)
