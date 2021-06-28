from typing import List

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QPushButton, QHBoxLayout
from PySide6.QtCore import QTimer, Signal, Qt
from UI.AppGlobals import AppGlobals
from Model.Program.ProgramInstance import ProgramInstance


class ConsoleViewer(QFrame):
    def __init__(self):
        super().__init__()
        consoleLayout = QVBoxLayout()
        clearButton = QPushButton("Clear")
        clearButton.clicked.connect(lambda: AppGlobals.ProgramRunner().ClearMessages())

        self._consoleText = QLabel()
        consoleLayout.addWidget(self._consoleText, alignment=Qt.AlignTop)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(consoleLayout, stretch=1)
        layout.addWidget(clearButton, stretch=0)
        self.setLayout(layout)

        timer = QTimer(self)
        timer.timeout.connect(self.Update)
        timer.start(30)

    def Update(self):
        text = ""
        for message in AppGlobals.ProgramRunner().GetMessages():
            text += message.text + "\n"
        if self._consoleText.text() != text:
            self._consoleText.setText(text)

