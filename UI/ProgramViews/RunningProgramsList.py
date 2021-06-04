from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton
from PySide6.QtCore import QTimer, Signal
from Model.Program.ProgramRunner import ProgramRunner


class RunningProgramsList(QWidget):
    onTextChanged = Signal()

    def __init__(self, parent, programRunner: ProgramRunner):
        super().__init__(parent)

        self._statusLabel = QLabel()

        clearButton = QPushButton("Clear")

        self._programRunner = programRunner
        clearButton.clicked.connect(self._programRunner.ClearErrors)

        layout = QVBoxLayout()

        layout.addWidget(clearButton)

        self.setLayout(layout)
        layout.addWidget(self._statusLabel)

        timer = QTimer(self)
        timer.timeout.connect(self.Update)
        timer.start(30)

    def Update(self):
        text = "Running Programs:\n"
        if not self._programRunner.runningPrograms:
            text += "\tNone.\n"
        for runningProgram in self._programRunner.runningPrograms:
            parentCount = 0
            current = runningProgram
            while current:
                parentCount += 1
                current = self._programRunner.runningPrograms[current].parentProgram
            text += "\t" * parentCount
            text += runningProgram.program.name + "\n"

        if self._programRunner.GetErrors():
            text += "Errors: \n"
            i = 0
            for error in self._programRunner.GetErrors():
                text += str(i) + "\t" + str(error.exception) + "\n"
                i += 1

        if text != self._statusLabel.text():
            self._statusLabel.setText(text)
            self.onTextChanged.emit()
