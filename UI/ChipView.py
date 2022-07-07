from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QFormLayout, \
    QLineEdit, QSpinBox
from PySide6.QtGui import QIcon, QImage, QPixmap, QColor, QKeyEvent
from PySide6.QtCore import QPoint, Qt, QSize, QTimer, QRectF
from UI.CustomGraphicsView import CustomGraphicsView, CustomGraphicsViewItem
from UI.UIMaster import UIMaster
from Data.Chip import Valve, Image, Text, ProgramPreset


class ChipView(QWidget):
    def __init__(self):
        super().__init__()
        self.graphicsView = CustomGraphicsView()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.layout().addWidget(self.graphicsView)

        self.toolPanel = QWidget(self)
        self.finishEditsButton = QPushButton()
        self.finishEditsButton.setToolTip("Finish editing")
        self.finishEditsButton.setIcon(
            ColoredIcon("Assets/Images/checkIcon.png", QColor(100, 100, 100)))
        self.finishEditsButton.setFixedSize(50, 50)
        self.finishEditsButton.setIconSize(QSize(30, 30))
        self.finishEditsButton.clicked.connect(lambda: self.SetEditing(False))

        self.editButton = QPushButton()
        self.editButton.setIcon(
            ColoredIcon("Assets/Images/Edit.png", QColor(100, 100, 100)))
        self.editButton.setToolTip("Edit chip")
        self.editButton.setFixedSize(50, 50)
        self.editButton.setIconSize(QSize(30, 30))
        self.editButton.clicked.connect(lambda: self.SetEditing(True))

        self.addValveButton = QPushButton()
        self.addValveButton.setToolTip("Add valve")
        self.addValveButton.setIcon(
            ColoredIcon("Assets/Images/plusIcon.png", QColor(100, 100, 100)))
        self.addValveButton.setFixedSize(30, 30)
        self.addValveButton.setIconSize(QSize(20, 20))
        self.addValveButton.clicked.connect(self.AddNewValve)

        toolPanelLayout = QVBoxLayout()
        toolPanelLayout.setContentsMargins(0, 0, 0, 0)
        toolPanelLayout.setSpacing(0)
        self.toolPanel.setLayout(toolPanelLayout)

        toolPanelLayout.addWidget(self.finishEditsButton, alignment=Qt.AlignHCenter)
        toolPanelLayout.addWidget(self.editButton)

        self.toolOptions = QWidget()
        toolOptionsLayout = QVBoxLayout()
        toolOptionsLayout.addWidget(self.addValveButton, alignment=Qt.AlignHCenter)
        self.toolOptions.setLayout(toolOptionsLayout)
        toolPanelLayout.addWidget(self.toolOptions)

        self.SetEditing(True)

    def resizeEvent(self, event):
        self.UpdateToolPanelPosition()
        super().resizeEvent(event)

    def UpdateToolPanelPosition(self):
        r = self.rect()

        padding = 20
        self.toolPanel.adjustSize()
        self.toolPanel.move(r.topLeft() + QPoint(padding, padding))

    def SetEditing(self, isEditing: bool):
        self.graphicsView.SetInteractive(isEditing)
        self.editButton.setVisible(not isEditing)
        self.finishEditsButton.setVisible(isEditing)
        self.toolOptions.setVisible(isEditing)
        self.UpdateToolPanelPosition()

    def AddNewValve(self):
        highestValveNumber = max(
            [x.solenoidNumber for x in UIMaster.Instance().currentChip.valves] + [-1])
        newValve = Valve()
        newValve.name = "Valve " + str(highestValveNumber + 1)
        newValve.solenoidNumber = highestValveNumber + 1
        UIMaster.Instance().currentChip.valves.append(newValve)
        self.graphicsView.AddItem(ValveItem(newValve), center=True, select=True)
        self.graphicsView.UpdateItemVisuals()

    def OpenChip(self):
        self.graphicsView.Clear()
        for valve in UIMaster.Instance().currentChip.valves:
            v = ValveItem(valve)
            v.SetRect(QRectF(*valve.rect))
            self.graphicsView.AddItem(v)


class ValveItem(CustomGraphicsViewItem):
    valveClosedStyle = """
    QPushButton {
    background-color: #f03535; 
    border: 1px solid black;
    }
    QPushButton::hover {
    background-color: #cc2d2d;
    }
    QPushButton::pressed {
    background-color: #b52828;
    }
    """

    valveOpenStyle = """
    QPushButton {
    background-color: #aeeb34; 
    border: 1px solid black;
    }
    QPushButton::hover {
    background-color: #99cf2d;
    }
    QPushButton::pressed {
    background-color: #86b528;
    }
    """

    def __init__(self, valve: Valve):
        super().__init__("Valve")
        self.valveWidget = QPushButton("Test")
        self.valveWidget.clicked.connect(self.Toggle)
        self.valveWidget.setMinimumSize(100, 100)
        self.valve = valve
        self.timer = QTimer(self.valveWidget)
        self.timer.timeout.connect(self.Update)
        self.timer.start(30)
        self._displayState = None

        self.nameField = QLineEdit()
        self.nameField.textEdited.connect(self.PushToValve)
        self.numberField = QSpinBox()
        self.numberField.valueChanged.connect(self.PushToValve)
        self.numberField.setMinimum(0)
        self.numberField.setMaximum(1000)
        self.fontSizeField = QSpinBox()
        self.fontSizeField.valueChanged.connect(self.PushToValve)
        self.SetWidget(self.valveWidget)
        inspectorWidget = QWidget()
        form = QFormLayout()
        form.addRow("Name", self.nameField)
        form.addRow("Solenoid", self.numberField)
        form.addRow("Text Size", self.fontSizeField)
        inspectorWidget.setLayout(form)
        self._updating = False
        self.SetInspector(inspectorWidget)
        self.Update()

    def SetRect(self, rect):
        self.valve.rect = [rect.topLeft().x(), rect.topRight().y(), rect.width(), rect.height()]
        UIMaster.Instance().modified = True
        super().SetRect(rect)

    def Remove(self) -> bool:
        UIMaster.Instance().currentChip.valves.remove(self.valve)
        return True

    def Toggle(self):
        r = UIMaster.Instance().rig
        r.SetSolenoidState(self.valve.solenoidNumber,
                           not r.GetSolenoidState(self.valve.solenoidNumber))

    def PushToValve(self):
        if self._updating:
            return
        self.valve.name = self.nameField.text()
        self.valve.solenoidNumber = self.numberField.value()
        self.valve.textSize = self.fontSizeField.value()
        UIMaster.Instance().modified = True

    def Update(self):
        self._updating = True
        if self.numberField.value() != self.valve.solenoidNumber:
            self.numberField.setValue(self.valve.solenoidNumber)
        if self.nameField.text() != self.valve.name:
            self.nameField.setText(self.valve.name)
        if self.fontSizeField.value() != self.valve.textSize:
            self.fontSizeField.setValue(self.valve.textSize)
        self.valveWidget.setText(self.valve.name + "\n(" + str(self.valve.solenoidNumber) + ")")
        newState = UIMaster.Instance().rig.GetSolenoidState(self.valve.solenoidNumber)
        if self.valveWidget.font().pointSize() != self.valve.textSize:
            f = self.valveWidget.font()
            f.setPointSize(self.valve.textSize)
            self.valveWidget.setFont(f)
        self._updating = False
        if newState == self._displayState:
            return
        self._displayState = newState
        self.valveWidget.setStyleSheet(self.valveOpenStyle if newState else self.valveClosedStyle)


class ColoredIcon(QIcon):
    def __init__(self, filename, color: QColor):
        pixmap = QPixmap(filename)
        replaced = QPixmap(pixmap.size())
        replaced.fill(color)
        replaced.setMask(pixmap.createMaskFromColor(Qt.transparent))
        super().__init__(replaced)
