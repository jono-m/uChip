from typing import Dict, List
from PySide6.QtWidgets import QFrame, QLabel, QListWidget, QPushButton, QMessageBox, QListWidgetItem, QVBoxLayout, \
    QFileDialog
from PySide6.QtCore import Signal, Qt, QSize
from Model.Program.Program import Program
from Model.Program.ProgramLibrary import ProgramLibrary
from Model.Program.ProgramInstance import ProgramInstance
from UI.AppGlobals import AppGlobals
from UI.ProgramViews.ProgramContextDisplay import ProgramContextDisplay


class ProgramList(QFrame):
    onProgramEditRequest = Signal(Program)

    def __init__(self, parent):
        super().__init__(parent)
        self._programsList = QListWidget()

        AppGlobals.Instance().onChipAddRemove.connect(self.SyncInstances)
        AppGlobals.Instance().onChipOpened.connect(self.SyncInstances)

        self._newButton = QPushButton("New Program")
        self._newButton.setProperty("Attention", True)
        self._newButton.clicked.connect(self.NewProgram)
        self._importButton = QPushButton("Import...")
        self._importButton.clicked.connect(self.ImportProgram)

        self._chipPrograms = ProgramListWidget()
        self._chipPrograms.onItemClicked.connect(lambda item: self.SelectProgram(item, self._chipPrograms, True))
        self._chipPrograms.onItemDoubleClicked.connect(self.EditProgram)
        self._libraryPrograms = ProgramListWidget()
        self._libraryPrograms.onItemClicked.connect(lambda item: self.SelectProgram(item, self._libraryPrograms, False))

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._chipPrograms)
        layout.addWidget(self._newButton)
        layout.addWidget(self._importButton)
        layout.addWidget(QLabel("Program Library"))
        layout.addWidget(self._libraryPrograms)

        self._contextDisplay = None

        self.setLayout(layout)

    def EditProgram(self, selectedProgram: 'ProgramListItem'):
        self.onProgramEditRequest.emit(selectedProgram.program)

    def SelectProgram(self, selectedProgram: 'ProgramListItem', listWidget: QListWidget, editable):
        self._contextDisplay = ProgramContextDisplay(self.topLevelWidget(), selectedProgram.instance, listWidget, editable)
        self._contextDisplay.onDelete.connect(self.DeleteProgram)
        self._contextDisplay.onEdit.connect(self.onProgramEditRequest)

    def SyncInstances(self):
        ProgramLibrary.ReloadLibrary(AppGlobals.Chip())
        self._chipPrograms.SyncInstances(AppGlobals.Chip().programs)
        self._libraryPrograms.SyncInstances(ProgramLibrary.Library())

    def ImportProgram(self):
        filename, filterType = QFileDialog.getOpenFileName(self, "Browse for Progra",
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
            return matches[0]
