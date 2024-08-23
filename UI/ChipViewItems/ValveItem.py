from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QPushButton, QLineEdit, QSpinBox, QWidget, QFormLayout
from UI.UIMaster import UIMaster
from UI.CustomGraphicsView import CustomGraphicsViewItem
from Data.Chip import Valve
from UI import Utilities
import re

# Valve stylesheets
valveClosedStyle = """
QPushButton {
background-color: #f03535; 
border: 1px solid black;
color: black;
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
color: black;
}
QPushButton::hover {
background-color: #99cf2d;
}
QPushButton::pressed {
background-color: #86b528;
}
"""


class ValveItem(CustomGraphicsViewItem):
    def __init__(self, valve: Valve):
        self.valve = valve

        # The actual widget is just a pushbutton!
        self.valveWidget = ValveItem.ResizeDelegate(self.OnResized)
        self.valveWidget.clicked.connect(self.Toggle)
        self.valveWidget.setMinimumSize(100, 100)
        self._displayState = None

        # The inspector just holds a name and a spinbox for solenoid number
        inspectorWidget = QWidget()
        form = QFormLayout()
        self.nameField = QLineEdit()
        self.nameField.textEdited.connect(self.RecordChanges)
        self.numberField = QSpinBox()
        self.numberField.valueChanged.connect(self.RecordChanges)
        self.numberField.setMinimum(0)
        self.numberField.setMaximum(1000)
        form.addRow("Name", self.nameField)
        form.addRow("Solenoid", self.numberField)
        inspectorWidget.setLayout(form)

        self.fadeWidget = QWidget(self.valveWidget)
        self.fadeWidget.setStyleSheet("background-color: rgba(255, 255, 255, 200);")

        super().__init__("Valve", self.valveWidget, inspectorWidget)
        super().SetRect(QRectF(*valve.rect))

    def OnResized(self, event):
        self.fadeWidget.move(0, 0)
        self.fadeWidget.setFixedSize(self.itemProxy.widget().size())

    def SetEnabled(self, state):
        super().SetEnabled(state)
        self.fadeWidget.setVisible(not state)

    class ResizeDelegate(QPushButton):
        def __init__(self, delegate):
            super().__init__()
            self.delegate = delegate

        def resizeEvent(self, event) -> None:
            super().resizeEvent(event)
            self.delegate(event)

    # Changes to the valve shape should be recorded.
    def SetRect(self, rect):
        super().SetRect(rect)
        self.RecordChanges()

    # Called when the valve is removed from the scene (either by the user or through loading a new
    # chip project.
    def OnRemoved(self) -> bool:
        UIMaster.Instance().currentChip.valves.remove(self.valve)
        UIMaster.Instance().modified = True
        return True

    # Duplicated valves take on the next highest solenoid number
    def Duplicate(self):
        highestValveNumber = max(
            [x.solenoidNumber for x in UIMaster.Instance().currentChip.valves] + [-1])
        newValve = Valve()

        # Regex used to match names if there is a number at the end.
        reMatch = re.match(r"(.*?)(\d+)", self.valve.name)
        if reMatch:
            nextNumber = int(reMatch.group(2)) + 1
            newValve.name = reMatch.group(1) + str(nextNumber)
            newValve.solenoidNumber = self.valve.solenoidNumber + 1
        else:
            newValve.name = self.valve.name
            newValve.solenoidNumber = highestValveNumber + 1
        UIMaster.Instance().currentChip.valves.append(newValve)
        UIMaster.Instance().modified = True
        return ValveItem(newValve)

    def Toggle(self):
        r = UIMaster.Instance().rig
        r.SetSolenoidState(self.valve.solenoidNumber,
                           not r.GetSolenoidState(self.valve.solenoidNumber))

    def RecordChanges(self):
        if self.isUpdating:
            return
        self.valve.name = self.nameField.text()
        self.valve.solenoidNumber = self.numberField.value()
        self.valve.rect = [self.GetRect().x(), self.GetRect().y(),
                           self.GetRect().width(), self.GetRect().height()]
        UIMaster.Instance().modified = True

    def Update(self):
        if self.numberField.value() != self.valve.solenoidNumber:
            self.numberField.setValue(self.valve.solenoidNumber)
        if self.nameField.text() != self.valve.name:
            self.nameField.setText(self.valve.name)

        text = self.valve.name + "\n(" + str(self.valve.solenoidNumber) + ")"
        if self.valveWidget.text() != text:
            self.valveWidget.setText(text)

        r = self.valveWidget.rect().size()
        r.setHeight(r.height() / 2)
        font = Utilities.ComputeAutofit(self.valveWidget.font(), r, self.valveWidget.text())
        if self.valveWidget.font().pixelSize() != font.pixelSize():
            self.valveWidget.setFont(font)
        currentState = UIMaster.Instance().rig.GetSolenoidState(self.valve.solenoidNumber)
        if currentState != self._displayState:
            self._displayState = currentState
            self.valveWidget.setStyleSheet(valveOpenStyle if currentState else valveClosedStyle)
