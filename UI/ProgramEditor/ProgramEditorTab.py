from PySide6.QtWidgets import QFrame, QSplitter, QHBoxLayout, QLineEdit, QVBoxLayout, QLabel
from Model.Program.Program import Program
from UI.AppGlobals import AppGlobals
from UI.ProgramEditor.CodeTextEditor import CodeTextEditor
from UI.ProgramEditor.ParameterEditor import ParameterEditor


class ProgramEditorTab(QFrame):
    def __init__(self, program: Program):
        super().__init__()

        AppGlobals.Instance().onChipOpened.connect(self.CheckForProgram)
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

        self._parameterEditor = ParameterEditor(program)
        self._parameterEditor.onParametersChanged.connect(self.ProgramEdited)

        sideLayout = QVBoxLayout()
        sideLayout.setContentsMargins(0, 0, 0, 0)
        sideLayout.setSpacing(0)
        sideLayout.addWidget(self._programNameField)
        sideLayout.addWidget(self._parameterEditor)
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
        self._parameterEditor.Save()
        self.modified = False
        AppGlobals.Instance().onChipModified.emit()

    def ProgramEdited(self):
        self.modified = True

    def CheckForProgram(self):
        if self.program not in AppGlobals.Chip().programs:
            self.deleteLater()
