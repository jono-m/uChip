from typing import List

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import Signal, Qt
from UI.AppGlobals import AppGlobals
from Model.Program.ProgramInstance import ProgramInstance


class RunningProgramsList(QFrame):
    onTextChanged = Signal()

    def __init__(self):
        super().__init__()

        self.runningProgramsListLayout = QVBoxLayout()
        self.runningProgramsListLayout.setContentsMargins(0, 0, 0, 0)
        self.runningProgramsListLayout.setSpacing(0)
        self.runningProgramsListLayout.setAlignment(Qt.AlignTop)

        self.runningProgramListItems: List[RunningProgramItem] = []

        self.setLayout(self.runningProgramsListLayout)

        AppGlobals.ProgramRunner().onInstanceChange.connect(self.Update)

    def Update(self):
        for runningProgramListItem in self.runningProgramListItems.copy():
            if not AppGlobals.ProgramRunner().IsRunning(runningProgramListItem.instance):
                self.runningProgramListItems.remove(runningProgramListItem)
                runningProgramListItem.deleteLater()
        for runningProgram in AppGlobals.ProgramRunner().runningPrograms.copy():
            item = self.FindItem(runningProgram)
            if not item:
                parent = AppGlobals.ProgramRunner().runningPrograms[runningProgram].parentProgram
                parentListItem = None
                if parent:
                    parentListItem = self.FindItem(parent)
                    if not parentListItem:
                        # Add it later, once the parent item has been added
                        continue
                newItem = RunningProgramItem(runningProgram, parentListItem is None)
                newItem.onStopClicked.connect(lambda instance: AppGlobals.ProgramRunner().Stop(instance))
                self.runningProgramListItems.append(newItem)
                if parentListItem:
                    parentListItem.runningChildrenListLayout.addWidget(newItem)
                else:
                    self.runningProgramsListLayout.addWidget(newItem)

        for i in range(len(self.runningProgramListItems)):
            self.runningProgramListItems[i].setProperty("IsEven", i % 2 == 0)

    def FindItem(self, programInstance: ProgramInstance):
        matches = [programItem for programItem in self.runningProgramListItems if
                   programItem.instance is programInstance]
        if matches:
            return matches[0]


class RunningProgramItem(QFrame):
    onStopClicked = Signal(ProgramInstance)

    def __init__(self, programInstance: ProgramInstance, stoppable=True):
        super().__init__()

        self.instance = programInstance

        programNameLabel = QLabel(programInstance.program.name)
        stopButton = QPushButton("STOP")
        stopButton.setProperty("BadAttention", True)
        stopButton.clicked.connect(lambda: self.onStopClicked.emit(self.instance))
        stopButton.setVisible(stoppable)
        infoLayout = QHBoxLayout()
        infoLayout.setContentsMargins(0, 0, 0, 0)
        infoLayout.setSpacing(0)
        infoLayout.addWidget(programNameLabel, stretch=1)
        infoLayout.addWidget(stopButton, stretch=0)

        self.runningChildrenListLayout = QVBoxLayout()
        self.runningChildrenListLayout.setContentsMargins(0, 0, 0, 0)
        self.runningChildrenListLayout.setSpacing(0)
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        mainLayout.addLayout(infoLayout)
        mainLayout.addLayout(self.runningChildrenListLayout)
        mainLayout.setAlignment(Qt.AlignTop)

        self.setLayout(mainLayout)
