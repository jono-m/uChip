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

        showButton = QPushButton()
        showButton.setText("Configure...")
        showButton.clicked.connect(self.ShowDialog)
        showButton.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

        self.mainLayout.addWidget(showButton)

        self.solenoidsScrollArea = QScrollArea()

        self.mainLayout.addWidget(self.solenoidsScrollArea)

        self.solenoidsContainer = QFrame()

        self.solenoidsScrollArea.setWidget(self.solenoidsContainer)

        self.layout = QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.solenoidsContainer.setLayout(self.layout)

        self.rig = rig

        self.rig.OnFlush.Register(self.UpdateDisplay)

        self.Repopulate()
        self.setModal(True)

    def ShowDialog(self):
        newWindow = RigConfigurationWindow(self.rig, parent=self)
        newWindow.finished.connect(self.Repopulate)
        newWindow.exec_()

    def Repopulate(self):
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().deleteLater()

        self.solenoidButtons = []

        for solenoidNumber in range(len(self.rig.solenoidStates)):
            newSolenoidButton = SolenoidButton(text=str(solenoidNumber))
            newSolenoidButton.clicked.connect(
                lambda checked=False, num=solenoidNumber: self.SolenoidClickedHandler(num))
            self.solenoidButtons.append(newSolenoidButton)

            row = int(solenoidNumber / 8)
            column = solenoidNumber % 8 + 2
            self.layout.addWidget(newSolenoidButton, row, column)

        if len(self.solenoidButtons) == 0:
            self.layout.addWidget(QLabel("No devices connected."), 0, 0)

        for rowNumber in range(int(len(self.rig.solenoidStates) / 8)):
            eightSet = range(rowNumber * 8, (rowNumber + 1) * 8)
            onButton = QPushButton("OPEN ALL")
            onButton.clicked.connect(
                lambda checked=False, es=eightSet: self.EightSetButtonPressed(es, True))
            offButton = QPushButton("CLOSE ALL")
            offButton.clicked.connect(
                lambda checked=False, es=eightSet: self.EightSetButtonPressed(es, False))
            self.layout.addWidget(onButton, rowNumber, 0)
            self.layout.addWidget(offButton, rowNumber, 1)

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

        self.setFixedSize(64, 64)
