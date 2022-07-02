from typing import Dict, List
from PySide6.QtWidgets import QFrame, QLabel, QListWidget, QPushButton, QMessageBox, QListWidgetItem, QVBoxLayout, \
    QFileDialog, QToolButton, QHBoxLayout
from PySide6.QtGui import QIcon
from PySide6.QtCore import Signal, Qt, QSize
from Data.Program.Program import Program
from Data.Program.ProgramInstance import ProgramInstance
from UI.AppGlobals import AppGlobals
from UI.ProgramViews.ProgramContextDisplay import ProgramContextDisplay


class ProgramList(QFrame):
    onProgramEditRequest = Signal(Program)

    def __init__(self, parent):
        super().__init__(parent)
        self._programsList = QListWidget()

        AppGlobals.Instance().onChipAddRemove.connect(self.SyncInstances)
        AppGlobals.Instance().onChipOpened.connect(self.SyncInstances)

        self._newButton = QToolButton()
        self._newButton.setIcon(QIcon("Assets/Images/plusIcon.png"))
        self._newButton.setProperty("Attention", True)
        self._newButton.clicked.connect(self.NewProgram)
        self._importButton = QToolButton()
        self._importButton.setIcon(QIcon("Assets/Images/importIcon.png"))
        self._importButton.clicked.connect(self.ImportProgram)

        self._chipPrograms = ProgramListWidget()
        self._chipPrograms.onItemClicked.connect(lambda item: self.SelectProgram(item, self._chipPrograms, True))
        self._chipPrograms.onItemDoubleClicked.connect(self.EditProgram)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        buttonLayout = QHBoxLayout()
        buttonLayout.setAlignment(Qt.AlignRight)
        buttonLayout.addWidget(self._newButton)
        buttonLayout.addWidget(self._importButton)
        buttonLayout.setSpacing(0)
        buttonLayout.setContentsMargins(0, 0, 0, 0)
        buttonWidget = QFrame()
        buttonWidget.setObjectName("ButtonPanel")
        buttonWidget.setLayout(buttonLayout)
        layout.addWidget(buttonWidget)
        layout.addWidget(self._chipPrograms)

        self._contextDisplay = None

        self.setLayout(layout)

    def EditProgram(self, selectedProgram: 'ProgramListItem'):
        self.onProgramEditRequest.emit(selectedProgram.program)

    def SelectProgram(self, selectedProgram: 'ProgramListItem', listWidget: QListWidget, editable):
        self._contextDisplay = ProgramContextDisplay(self.topLevelWidget(), selectedProgram.instance, listWidget,
                                                     editable)
        self._contextDisplay.onDelete.connect(self.DeleteProgram)
        self._contextDisplay.onEdit.connect(self.onProgramEditRequest)

    def SyncInstances(self):
        self._chipPrograms.SyncInstances(AppGlobals.Chip().programs)

    def ImportProgram(self):
        filename, filterType = QFileDialog.getOpenFileName(self, "Browse for Program",
                                                           filter="μChip Program (*.ucp)")
        if filename:
            program = Program.LoadFromFile(filename)
            AppGlobals.Chip().programs.append(program)
            AppGlobals.Instance().onChipAddRemove.emit()

    def NewProgram(self):
        newProgram = Program()
        AppGlobals.Chip().programs.append(newProgram)
        AppGlobals.Instance().onChipAddRemove.emit()
        for item in [self._chipPrograms.item(row) for row in range(self._chipPrograms.count())]:
            if item.program is newProgram:
                self._chipPrograms.setCurrentItem(item)
                self.onProgramEditRequest.emit(newProgram)
                return

    def DeleteProgram(self, program: Program):
        if QMessageBox.question(self, "Confirm Deletion",
                                "Are you sure you want to delete " + program.name + "?") is QMessageBox.Yes:
            AppGlobals.Chip().programs.remove(program)
            AppGlobals.Instance().onChipAddRemove.emit()


class ProgramListItem(QListWidgetItem):
    def __init__(self, program: Program, instance: ProgramInstance):
        super().__init__(program.name)
        self.program = program
        self.instance = instance


class ProgramListWidget(QListWidget):
    onItemClicked = Signal(ProgramListItem)
    onItemDoubleClicked = Signal(ProgramListItem)

    def __init__(self):
        super().__init__()

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.itemClicked.connect(self.onItemClicked.emit)
        self.itemDoubleClicked.connect(self.onItemDoubleClicked.emit)

        self._instances: Dict[Program, ProgramInstance] = {}

    def SyncInstances(self, programs: List[Program]):
        for program in programs:
            if program not in self._instances:
                self._instances[program] = ProgramInstance(program)
        for program in self._instances.copy():
            if program not in programs:
                del self._instances[program]
            else:
                self._instances[program].SyncParameters()
        self.RefreshList(programs)

    def RefreshList(self, programs: List[Program]):
        self.blockSignals(True)

        self.clear()
        for program in programs:
            self.addItem(ProgramListItem(program, self._instances[program]))

        self.blockSignals(False)

    def ProgramItem(self, program: Program):
        matches = [item for item in [self.item(row) for row in range(self.count())] if
                   item.program is program]
        if matches:
            return matches[0]from Data.Program.ProgramInstance import ProgramInstance, Program

from PySide6.QtWidgets import QFrame, QVBoxLayout, QApplication, QPushButton
from PySide6.QtCore import Qt, QEvent, Signal
from UI.ProgramViews.ProgramInstanceWidget import ProgramInstanceWidget


class ProgramContextDisplay(QFrame):
    onDelete = Signal(Program)
    onEdit = Signal(Program)

    def __init__(self, parent, programInstance: ProgramInstance, listWidget, editable):
        super().__init__(parent)

        self._programInstance = programInstance

        self.listWidget = listWidget

        container = QFrame()
        self.setAutoFillBackground(True)
        clayout = QVBoxLayout()
        clayout.setContentsMargins(0, 0, 0, 0)
        clayout.setSpacing(0)
        self.setLayout(clayout)
        self.layout().addWidget(container)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        container.setLayout(layout)

        QApplication.instance().installEventFilter(self)

        self._instanceWidget = ProgramInstanceWidget(programInstance)
        self._instanceWidget.SetShowAllParameters(True)
        self._instanceWidget.ownsInstance = False
        layout.addWidget(self._instanceWidget)

        if editable:
            self._editButton = QPushButton("Edit")
            self._editButton.clicked.connect(lambda: self.onEdit.emit(self._programInstance.program))
            self._deleteButton = QPushButton("Delete")
            self._deleteButton.clicked.connect(lambda: self.onDelete.emit(self._programInstance.program))
            layout.addWidget(self._editButton)
            layout.addWidget(self._deleteButton)

        self.setFocusPolicy(Qt.ClickFocus)

        self.Reposition()

    def Reposition(self):
        self.adjustSize()
        self.show()
        self.raise_()
        topLeft = self.mapToGlobal(self.rect().topLeft())

        matches = [item for item in [self.listWidget.item(row) for row in range(self.listWidget.count())] if
                   item.program is self._programInstance.program]
        if matches:
            listWidgetItem = matches[0]
        else:
            return

        rect = listWidgetItem.listWidget().rectForIndex(
            listWidgetItem.listWidget().indexFromItem(listWidgetItem))
        topRightItem = listWidgetItem.listWidget().mapToGlobal(rect.topRight())
        delta = topRightItem - topLeft
        self.move(self.pos() + delta)

    def eventFilter(self, watched, event) -> bool:
        if self.isVisible() and event.type() == QEvent.MouseButtonPress:
            widget = QApplication.widgetAt(event.globalPos())
            while widget:
                if widget is self:
                    return False
                widget = widget.parent()
            self.deleteLater()
        return False

    def event(self, e) -> bool:
        if e.type() == QEvent.LayoutRequest:
            self.adjustSize()
        return super().event(e)from PySide6.QtWidgets import QFrame, QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit, QVBoxLayout, QLabel, QHBoxLayout, \
    QSizePolicy
from PySide6.QtCore import Signal
from Data.Program.Data import DataType, DataValueType
from UI.ProgramViews.ChipDataSelection import ChipDataSelection
from typing import List


class DataValueWidget(QFrame):
    dataChanged = Signal()

    def __init__(self, dataType: DataType, listType: DataType = None):
        super().__init__()

        self.dataType = dataType

        if self.dataType is DataType.INTEGER:
            self.field = QSpinBox()
            self.field.valueChanged.connect(lambda: self.dataChanged.emit())
        elif self.dataType is DataType.FLOAT:
            self.field = QDoubleSpinBox()
            self.field.valueChanged.connect(lambda: self.dataChanged.emit())
        elif self.dataType is DataType.BOOLEAN:
            self.field = QComboBox()
            self.field.addItem("True", True)
            self.field.addItem("False", False)
            self.field.currentIndexChanged.connect(lambda: self.dataChanged.emit())
        elif self.dataType is DataType.STRING:
            self.field = QLineEdit()
            self.field.textChanged.connect(lambda: self.dataChanged.emit())
        elif self.dataType is DataType.VALVE or self.dataType is DataType.PROGRAM_PRESET:
            self.field = ChipDataSelection(self.dataType)
            self.field.currentIndexChanged.connect(lambda: self.dataChanged.emit())
        elif self.dataType is DataType.LIST and listType:
            self.field = ListDataSelection(listType)
            self.field.dataChanged.connect(lambda: self.dataChanged.emit())
        else:
            return
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.field)

        self.field.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setLayout(layout)

    def GetData(self):
        if self.dataType is DataType.INTEGER or self.dataType is DataType.FLOAT:
            return self.field.value()
        elif self.dataType is DataType.BOOLEAN or self.dataType is DataType.VALVE or self.dataType is DataType.PROGRAM_PRESET:
            return self.field.currentData()
        elif self.dataType is DataType.STRING:
            return self.field.text()
        elif self.dataType is DataType.LIST:
            return self.field.GetList()

    def Update(self, data: DataValueType):
        if self.dataType is DataType.INTEGER:
            self.field.setValue(data)
        elif self.dataType is DataType.FLOAT:
            self.field.setValue(data)
        elif self.dataType is DataType.BOOLEAN:
            self.field.setCurrentText(str(data))
        elif self.dataType is DataType.STRING:
            self.field.setText(data)
        elif self.dataType is DataType.VALVE or self.dataType is DataType.PROGRAM_PRESET:
            self.field.Select(data)
        elif self.dataType is DataType.LIST:
            self.field.Prepare(data)


class ListDataSelection(QFrame):
    dataChanged = Signal()

    def __init__(self, listDataType: DataType):
        super().__init__()
        self.listDataType = listDataType
        countLabel = QLabel("Count: ")
        self.countField = QSpinBox()
        self.countField.setMinimum(0)
        self.countField.setMaximum(200)
        self.countField.valueChanged.connect(lambda: self.dataChanged.emit())

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        titleLayout = QHBoxLayout()
        titleLayout.setContentsMargins(0, 0, 0, 0)
        titleLayout.setSpacing(0)
        titleLayout.addWidget(countLabel)
        titleLayout.addWidget(self.countField)
        layout.addLayout(titleLayout)
        self.setLayout(layout)

        self._fields: List[DataValueWidget] = []

    def Prepare(self, data: List[DataValueType]):
        self.countField.setValue(len(data))

        pool = len(self._fields)
        needed = len(data)
        delta = needed - pool

        for i in range(abs(delta)):
            if delta > 0:
                valueWidget = DataValueWidget(self.listDataType)
                valueWidget.dataChanged.connect(lambda: self.dataChanged.emit())
                self.layout().addWidget(valueWidget)
                self._fields.append(valueWidget)
            else:
                self._fields.pop().deleteLater()

        for i in range(needed):
            self._fields[i].Update(data[i])

    def GetList(self):
        count = self.countField.value()
        mainList = [field.GetData() for field in self._fields] + \
                   [self.listDataType.GetDefaultValue()] * (count - len(self._fields))
        return mainList[:count]
from typing import List

from PySide6.QtWidgets import QComboBox
from Data.Program.Data import DataType
from UI.AppGlobals import AppGlobals


class ChipDataSelection(QComboBox):
    def __init__(self, dataType: DataType):
        super().__init__()

        self.dataType = dataType

        AppGlobals.Instance().onChipAddRemove.connect(self.Repopulate)
        AppGlobals.Instance().onChipDataModified.connect(self.UpdateNames)

        self.Repopulate()

    def Select(self, data):
        for index in range(self.count()):
            if self.itemData(index) is data:
                self.setCurrentIndex(index)
                return

    def ItemsToRepopulate(self) -> List:
        if self.dataType is DataType.VALVE:
            return AppGlobals.Chip().valves
        if self.dataType is DataType.PROGRAM_PRESET:
            return AppGlobals.Chip().programPresets

    def Repopulate(self):
        self.blockSignals(True)
        lastSelected = self.currentData()
        self.clear()
        self.addItem("None", None)
        for item in self.ItemsToRepopulate():
            self.addItem(item.name, item)
            if item is lastSelected:
                self.setCurrentIndex(self.count() - 1)
        self.blockSignals(False)

    def UpdateNames(self):
        for index in range(self.count()):
            item = self.itemData(index)
            if item:
                self.setItemText(index, item.name)
