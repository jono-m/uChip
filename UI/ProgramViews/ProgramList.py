from typing import Optional, Dict
from PySide6.QtWidgets import QWidget, QLabel, QListWidget, QPushButton, QMessageBox, QListWidgetItem, QVBoxLayout, \
    QApplication, QLineEdit
from PySide6.QtCore import Signal, Qt, QTimer, QEvent
from Model.Program.Program import Program
from Model.Program.ProgramRunner import ProgramRunner
from Model.Program.ProgramInstance import ProgramInstance
from UI.AppGlobals import AppGlobals
from UI.ProgramViews.ProgramParameterList import ProgramParameterList


class ProgramList(QWidget):
    onProgramEditRequest = Signal(Program)

    def __init__(self, parent, programRunner: ProgramRunner):
        super().__init__(parent)
        self._programsLabel = QLabel("Programs")
        self._programsList = QListWidget()
        self._programsList.itemClicked.connect(self.SelectProgram)

        AppGlobals.Instance().onChipModified.connect(self.SyncInstances)

        self._instances: Dict[Program, ProgramInstance] = {}

        self._newButton = QPushButton("Create New Program")
        self._newButton.clicked.connect(self.NewProgram)

        layout = QVBoxLayout()
        layout.addWidget(self._programsLabel)
        layout.addWidget(self._programsList)
        layout.addWidget(self._newButton)

        self.setLayout(layout)

        self._programRunner = programRunner

        AppGlobals.Instance().onChipOpened.connect(self.RefreshList)

        self._contextView = ProgramContextDisplay(self.topLevelWidget())
        self._contextView.onProgramDelete.connect(self.RefreshList)
        self._contextView.onProgramEditRequest.connect(self.onProgramEditRequest.emit)
        self._contextView.onProgramRun.connect(lambda instance: self._programRunner.Run(instance))

    def SelectProgram(self, selectedProgram: 'ProgramListItem'):
        self._contextView.SetProgramItem(selectedProgram)

    def SyncInstances(self):
        for program in AppGlobals.Chip().programs:
            if program not in self._instances:
                self._instances[program] = ProgramInstance(program)
        for program in self._instances.copy():
            if program not in AppGlobals.Chip().programs:
                del self._instances[program]
            else:
                self._instances[program].SyncParameters()
        self.RefreshList()

    def NewProgram(self):
        newProgram = Program()
        AppGlobals.Chip().programs.append(newProgram)
        AppGlobals.Instance().onChipModified.emit()
        for item in [self._programsList.item(row) for row in self._programsList.count()]:
            if item.program is newProgram:
                self._programsList.setCurrentItem(item)
                self._contextView.SetProgramItem(item, True)
                return

    def ProgramItem(self, program: Program):
        matches = [item for item in [self._programsList.item(row) for row in range(self._programsList.count())] if
                   item.program is program]
        if matches:
            return matches[0]

    def RefreshList(self):
        self._programsList.blockSignals(True)

        self._programsList.clear()
        for program in AppGlobals.Chip().programs:
            self._programsList.addItem(ProgramListItem(program, self._instances[program]))

        self._programsList.blockSignals(False)


class ProgramListItem(QListWidgetItem):
    def __init__(self, program: Program, instance: ProgramInstance):
        super().__init__(program.name)
        self.program = program
        self.instance = instance


class ProgramContextDisplay(QWidget):
    onProgramRun = Signal(ProgramInstance)
    onProgramDelete = Signal()
    onProgramChanged = Signal()
    onProgramEditRequest = Signal(Program)

    def __init__(self, parent):
        super().__init__(parent)

        container = QWidget()
        self.setAutoFillBackground(True)
        clayout = QVBoxLayout()
        clayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(clayout)
        self.layout().addWidget(container)

        self._nameField = QLineEdit()
        self._nameField.textChanged.connect(self.UpdateProgram)
        layout = QVBoxLayout()
        container.setLayout(layout)
        layout.addWidget(self._nameField)
        self.raise_()

        runButton = QPushButton("Run")
        runButton.clicked.connect(self.RunProgram)

        editButton = QPushButton("Edit")
        editButton.clicked.connect(self.EditProgram)

        deleteButton = QPushButton("Delete")
        deleteButton.clicked.connect(self.DeleteProgram)

        self._parameterList = ProgramParameterList()

        QApplication.instance().installEventFilter(self)

        layout.addWidget(self._parameterList)
        layout.addWidget(runButton)
        layout.addWidget(editButton)
        layout.addWidget(deleteButton)

        self._program = None
        self._programItem: Optional[ProgramListItem] = None
        self._instance: Optional[ProgramInstance] = None

        self.setFocusPolicy(Qt.ClickFocus)
        self.Clear()

        timer = QTimer(self)
        timer.timeout.connect(self.Reposition)
        timer.start(30)

    def SetProgramItem(self, programItem: ProgramListItem, focusText=False):
        self._program = programItem.program
        self._programItem = programItem
        self._instance = programItem.instance
        self._instance.SyncParameters()

        self._parameterList.SetProgramInstance(programItem.instance)

        self._nameField.setText(self._program.name)

        self.setVisible(True)
        if focusText:
            self._nameField.setFocus()
            self._nameField.selectAll()
        else:
            self.setFocus()
        self.Reposition()
        self.raise_()

    def Clear(self):
        self._program = None
        self._programItem = None
        self.setVisible(False)

    def Reposition(self):
        if not self.isVisible():
            return
        self.resize(self.sizeHint())
        topLeft = self.mapToGlobal(self.rect().topLeft())

        rect = self._programItem.listWidget().rectForIndex(
            self._programItem.listWidget().indexFromItem(self._programItem))
        topRightItem = self._programItem.listWidget().mapToGlobal(rect.topRight())
        delta = topRightItem - topLeft
        self.move(self.pos() + delta)

    def eventFilter(self, watched, event) -> bool:
        if self.isVisible() and event.type() == QEvent.MouseButtonPress:
            widget = QApplication.widgetAt(event.globalPos())
            while widget:
                if widget is self:
                    return False
                widget = widget.parent()
            self.Clear()
        return False

    def DeleteProgram(self):
        if QMessageBox.question(self, "Confirm Deletion",
                                "Are you sure you want to delete " + self._program.name + "?") is QMessageBox.Yes:
            AppGlobals.Chip().programs.remove(self._program)
            self.onProgramDelete.emit()
            self.Clear()
            AppGlobals.Instance().onChipModified.emit()

    def UpdateProgram(self):
        self._program.name = self._nameField.text()
        self._programItem.setText(self._program.name)
        self.onProgramChanged.emit()
        AppGlobals.Instance().onChipModified.emit()

    def EditProgram(self):
        self.onProgramEditRequest.emit(self._program)

    def RunProgram(self):
        self.onProgramRun.emit(self._instance.Clone())
