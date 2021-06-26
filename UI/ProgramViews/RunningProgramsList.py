from typing import List

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer, Signal, Qt
from UI.AppGlobals import AppGlobals
from Model.Program.ProgramInstance import ProgramInstance


class RunningProgramsList(QFrame):
    onTextChanged = Signal()

    def __init__(self):
        super().__init__()

        self.runningProgramsListLayout = QVBoxLayout()
        self.runningProgramsListLayout.setContentsMargins(0, 0, 0, 0)
        self.runningProgramsListLayout.setSpacing(0)

        self.runningProgramListItems: List[RunningProgramItem] = []

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(self.runningProgramsListLayout)
        self.setLayout(layout)

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
                newItem.onStopClicked.connect(lambda instance: AppGlobals.ProgramRunner().Stop(instance))
                self.runningProgramListItems.append(newItem)
                if parentListItem:
                    parentListItem.runningChildrenListLayout.addWidget(newItem)
                else:
                    self.runningProgramsListLayout.addWidget(newItem)

    def FindItem(self, programInstance: ProgramInstance):
        matches = [programItem for programItem in self.runningProgramListItems if
                   programItem.instance is programInstance]
        if matches:
            return matches[0]


class RunningProgramItem(QFrame):
    onStopClicked = Signal(ProgramInstance)

    def __init__(self, programInstance: ProgramInstance):
        super().__init__()

        self.instance = programInstance

        programNameLabel = QLabel(programInstance.program.name)
        stopButton = QPushButton("STOP")
        stopButton.clicked.connect(lambda: self.onStopClicked.emit(self.instance))

        infoLayout = QHBoxLayout()
        infoLayout.setContentsMargins(0, 0, 0, 0)
        infoLayout.setSpacing(0)
        infoLayout.addWidget(programNameLabel)
        infoLayout.addWidget(stopButton)

        self.runningChildrenListLayout = QVBoxLayout()
        self.runningChildrenListLayout.setContentsMargins(0, 0, 0, 0)
        self.runningChildrenListLayout.setSpacing(0)
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        mainLayout.addLayout(infoLayout)
        mainLayout.addLayout(self.runningChildrenListLayout)

        self.setLayout(mainLayout)
