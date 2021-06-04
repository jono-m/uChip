from typing import Dict
from PySide6.QtWidgets import QWidget, QLabel, QListWidget, QPushButton, QMessageBox, QListWidgetItem, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from Model.Program.Program import Program
from Model.Program.ProgramInstance import ProgramInstance
from UI.AppGlobals import AppGlobals
from UI.ProgramViews.ProgramContextDisplay import ProgramContextDisplay


class ProgramList(QWidget):
    onProgramEditRequest = Signal(Program)

    def __init__(self, parent):
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

        AppGlobals.Instance().onChipOpened.connect(self.RefreshList)

    def EditProgram(self, selectedProgram: 'ProgramListItem'):
        self.onProgramEditRequest.emit(selectedProgram.program)

    def SelectProgram(self, selectedProgram: 'ProgramListItem'):
        contextDisplay = ProgramContextDisplay(self.topLevelWidget(), selectedProgram.instance, self._programsList)
        contextDisplay.onDelete.connect(self.DeleteProgram)
        contextDisplay.onEdit.connect(self.onProgramEditRequest)

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
        for item in [self._programsList.item(row) for row in range(self._programsList.count())]:
            if item.program is newProgram:
                self._programsList.setCurrentItem(item)
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

    def DeleteProgram(self, program: Program):
        if QMessageBox.question(self, "Confirm Deletion",
                                "Are you sure you want to delete " + program.name + "?") is QMessageBox.Yes:
            AppGlobals.Chip().programs.remove(program)
            AppGlobals.Instance().onChipModified.emit()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Delete:
            if self._programsList.currentItem():
                self.DeleteProgram(self._programsList.currentItem().program)


class ProgramListItem(QListWidgetItem):
    def __init__(self, program: Program, instance: ProgramInstance):
        super().__init__(program.name)
        self.program = program
        self.instance = instance
