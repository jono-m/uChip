from UI.RigView.RigConfigurationWindow import *
from UI.Util import *


class RigViewWidget(QDialog):
    def __init__(self, rig: Rig, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowFlags(Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)

        self.setWindowTitle("Rig")

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)
        self.setLayout(self.mainLayout)

        self.solenoidButtons: typing.List[SolenoidButton] = []

        self.configureButton = QPushButton()
        self.configureButton.setText("Configure Rig...")
        self.configureButton.clicked.connect(self.ShowDialog)

        self.solenoidsContainer = QFrame()

        self.mainLayout.addWidget(self.configureButton)
        self.mainLayout.addWidget(QLabel("Solenoids"))

        self.scrollArea = QScrollArea()
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.solenoidsContainer)

        self.mainLayout.addWidget(self.scrollArea)

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
                currentLayout.setAlignment(Qt.AlignLeft)
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
            self.solenoidsLayout.addWidget(QLabel("No devices connected."))

        self.solenoidsContainer.adjustSize()
        self.scrollArea.setFixedWidth(self.solenoidsContainer.width() + self.scrollArea.verticalScrollBar().width())
        self.adjustSize()
        self.UpdateDisplay()

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
            self.solenoidButtons[i].setProperty("IsDriven", not self.solenoidButtons[i].isEnabled())
            self.solenoidButtons[i].setStyle(self.solenoidButtons[i].style())
            self.solenoidButtons[i].update()
            if self.solenoidButtons[i].isEnabled():
                self.solenoidButtons[i].setToolTip("")
            else:
                self.solenoidButtons[i].setToolTip("Driven by chip.")


class SolenoidButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCheckable(True)
