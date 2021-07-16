from PySide6.QtWidgets import QFrame, QSplitter, QHBoxLayout, QLineEdit, QVBoxLayout, QLabel, QPlainTextEdit
from PySide6.QtCore import Signal, Qt
from Model.Program.Program import Program
from UI.AppGlobals import AppGlobals
from UI.ProgramEditor.CodeTextEditor import CodeTextEditor
from UI.ProgramEditor.ParameterEditor import ParameterEditor
from pathlib import Path


class ProgramEditorTab(QFrame):
    onModified = Signal()

    def __init__(self, program: Program):
        super().__init__()

        AppGlobals.Instance().onChipModified.connect(self.CheckForProgram)

        self.program = program
        self.modified = False
        self.codeEditor = CodeTextEditor()

        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        layout.addWidget(splitter)

        self._programNameField = QLineEdit(program.name)
        self._programNameField.textChanged.connect(self.UpdateProgramName)

        descriptionLabel = QLabel("Description")
        descriptionLabel.setObjectName("DescriptionLabel")
        descriptionLabel.setAlignment(Qt.AlignCenter)
        self._descriptionField = QPlainTextEdit(program.description)
        self._descriptionField.textChanged.connect(self.UpdateProgramName)

        self._parameterEditor = ParameterEditor(program)
        self._parameterEditor.onParametersChanged.connect(self.ProgramEdited)

        sideLayout = QVBoxLayout()
        sideLayout.setContentsMargins(0, 0, 0, 0)
        sideLayout.setSpacing(0)
        sideLayout.addWidget(self._programNameField)
        sideLayout.addWidget(self._parameterEditor, stretch=1)
        sideLayout.addWidget(descriptionLabel)
        sideLayout.addWidget(self._descriptionField, stretch=0)
        sideWidget = QFrame()
        sideWidget.setLayout(sideLayout)

        splitter.addWidget(sideWidget)
        splitter.addWidget(self.codeEditor)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.codeEditor.SetCode(self.program.script)

        self.codeEditor.codeChanged.connect(self.ProgramEdited)

    def UpdateProgramName(self):
        self.ProgramEdited()

    def SaveProgram(self):
        self.program.script = self.codeEditor.Code()
        self.program.name = self._programNameField.text()
        self.program.description = self._descriptionField.toPlainText()
        self._parameterEditor.Save()
        self.modified = False
        AppGlobals.Instance().onChipModified.emit()

    def ExportProgram(self, path: Path):
        self.SaveProgram()
        self.program.Export(path)

    def ProgramEdited(self):
        self.modified = True
        self.onModified.emit()

    def CheckForProgram(self):
        if self.program not in AppGlobals.Chip().programs:
            self.deleteLater()
