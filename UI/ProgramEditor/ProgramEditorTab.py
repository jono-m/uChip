from PySide6.QtWidgets import QWidget, QHBoxLayout
from Model.Program.Program import Program
from UI.AppGlobals import AppGlobals
from UI.ProgramEditor.CodeTextEditor import CodeTextEditor
from UI.ProgramEditor.ParameterEditor import ParameterEditor


class ProgramEditorTab(QWidget):
    def __init__(self, program: Program):
        super().__init__()

        AppGlobals.Instance().onChipOpened.connect(self.CheckForProgram)
        AppGlobals.Instance().onChipModified.connect(self.CheckForProgram)

        self.program = program
        self.modified = False
        self.codeEditor = CodeTextEditor()

        layout = QHBoxLayout()
        self.setLayout(layout)

        self._parameterEditor = ParameterEditor(program)
        self._parameterEditor.onParametersChanged.connect(self.ProgramEdited)

        layout.addWidget(self._parameterEditor, stretch=0)
        layout.addWidget(self.codeEditor, stretch=1)

        self.codeEditor.SetCode(self.program.script)

        self.codeEditor.codeChanged.connect(self.ProgramEdited)

    def SaveProgram(self):
        self.program.script = self.codeEditor.Code()
        self._parameterEditor.Save()
        self.modified = False
        AppGlobals.Instance().onChipModified.emit()

    def ProgramEdited(self):
        self.modified = True

    def CheckForProgram(self):
        if self.program not in AppGlobals.Chip().programs:
            self.deleteLater()


