from typing import List

4
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer, Signal
from UI.AppGlobals import AppGlobals
from Model.Program.ProgramInstance import ProgramInstance


class RunningProgramsList(QWidget):
    onTextChanged = Signal()

    def __init__(self):
        super().__init__()

        self.runningProgramsListLayout = QVBoxLayout()
        self.setLayout(self.runningProgramsListLayout)

        self.runningProgramListItems: List[RunningProgramItem] = []

        timer = QTimer(self)
        timer.timeout.connect(self.Update)
        timer.start(30)

    def Update(self):
        for runningProgramListItem in self.runningProgramListItems.copy():
            if not AppGlobals.ProgramRunner().IsRunning(runningProgramListItem.instance):
                self.runningProgramListItems.remove(runningProgramListItem)
                runningProgramListItem.deleteLater()
        for runningProgram in AppGlobals.ProgramRunner().runningPrograms:
            item = self.FindItem(runningProgram)
            if not item:
                parent = AppGlobals.ProgramRunner().runningPrograms[runningProgram].parentProgram
                parentListItem = None
                if parent:
                    parentListItem = self.FindItem(parent)
                    if not parentListItem:
                        # Add it later, once the parent item has been added
                        continue
                newItem = RunningProgramItem(runningProgram)
                self.runningProgramListItems.append(newItem)
                if parentListItem:
                    parentListItem.runningChildrenListLayout.addWidget(newItem)
                else:
                    self.runningProgramsListLayout.addWidget(newItem)

    def FindItem(self, programInstance: ProgramInstance):
        matches = [programItem for programItem in self.runningProgramListItems if programItem.instance is programInstance]
        if matches:
            return matches[0]


class RunningProgramItem(QWidget):
    onStopClicked = Signal(ProgramInstance)

    def __init__(self, programInstance: ProgramInstance):
        super().__init__()

        self.instance = programInstance

        programNameLabel = QLabel(programInstance.program.name)
        stopButton = QPushButton("STOP")
        stopButton.clicked.connect(lambda: self.onStopClicked.emit(self.instance))

        infoLayout = QHBoxLayout()
        infoLayout.addWidget(programNameLabel)
        infoLayout.addWidget(stopButton)

        self.runningChildrenListLayout = QVBoxLayout()

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(infoLayout)
        mainLayout.addLayout(self.runningChildrenListLayout)

        self.setLayout(mainLayout)
