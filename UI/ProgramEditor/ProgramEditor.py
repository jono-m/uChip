from typing import Optional
from PySide6.QtWidgets import QWidget, QPlainTextEdit, QHBoxLayout, QListWidget, QPushButton, QVBoxLayout, \
    QListWidgetItem, QMessageBox, QLabel, QLineEdit
from PySide6.QtCore import QTimer
from Model.Chip import Chip, Program


class ProgramEditor(QWidget):
    def __init__(self):
        super().__init__()
        self._saveButton = QPushButton("Save")
        self._saveButton.clicked.connect(self.SaveProgram)
        self._saveButton.setEnabled(False)

        self._openProgramLabel = QLineEdit("")
        self._openProgramLabel.textChanged.connect(self.ProgramEdited)

        self._textEdit = QPlainTextEdit()
        self._textEdit.setEnabled(False)

        layout = QHBoxLayout()
        self.setLayout(layout)
        programTextEditorLayout = QVBoxLayout()
        programTitleButtonLayout = QHBoxLayout()
        programTitleButtonLayout.addWidget(self._openProgramLabel)
        programTitleButtonLayout.addWidget(self._saveButton)
        programTextEditorLayout.addLayout(programTitleButtonLayout)
        programTextEditorLayout.addWidget(self._textEdit)

        layout.addLayout(programTextEditorLayout, stretch=1)

        self._textEdit.textChanged.connect(self.ProgramEdited)

        self._currentProgram: Optional[Program] = None
        self._modified = False
        self._chip: Optional[Chip] = None

    def SaveProgram(self):
        self._currentProgram.script = self._textEdit.toPlainText()
        self._currentProgram.name = self._openProgramLabel.text()
        for row in range(self._programsList.count()):
            if self._programsList.item(row).program == self._currentProgram:
                self._programsList.item(row).setText(self._currentProgram.name)
        self._modified = False
        self.UpdateState()

    def ConfirmChange(self):
        if self._modified:
            ret = QMessageBox.warning(self, "Confirm", "The program has been modified.\nDo you want to save changes?",
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
            if ret is QMessageBox.Save:
                self.SaveProgram()
            elif ret is QMessageBox.Cancel:
                return False
        return True

    def OpenProgram(self, newProgram: Program):
        self._currentProgram = newProgram
        self._textEdit.setPlainText(self._currentProgram.script)
        self._openProgramLabel.setText(self._currentProgram.name)
        self._modified = False
        self.UpdateState()

    def LoadChip(self, chip: Chip):
        self._chip = chip
        self.RefreshList()

    def ProgramEdited(self):
        self._modified = True
        self._saveButton.setEnabled(True)
        self.UpdateState()

    def UpdateState(self):
        self._saveButton.setVisible(bool(self._currentProgram))
        self._openProgramLabel.setVisible(bool(self._currentProgram))
        self._textEdit.setEnabled(bool(self._currentProgram))

        if not self._currentProgram:
            return

        self._saveButton.setEnabled(self._modified)

