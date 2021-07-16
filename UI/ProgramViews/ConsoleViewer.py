from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QScrollArea
from PySide6.QtCore import Qt
from UI.AppGlobals import AppGlobals
from Model.Program.ProgramRunner import ProgramRunnerMessage


class ConsoleViewer(QFrame):
    def __init__(self):
        super().__init__()
        scrollArea = QScrollArea()
        consoleArea = QFrame()
        scrollArea.setWidget(consoleArea)
        scrollArea.setWidgetResizable(True)

        self._consoleLayout = QVBoxLayout()
        self._consoleLayout.setSpacing(0)
        self._consoleLayout.setContentsMargins(0, 0, 0, 0)
        self._consoleLayout.setAlignment(Qt.AlignTop)
        consoleArea.setLayout(self._consoleLayout)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(scrollArea, stretch=1)
        clearButton = QPushButton("Clear")
        clearButton.clicked.connect(lambda: AppGlobals.ProgramRunner().ClearMessages())
        layout.addWidget(clearButton, stretch=0)
        self.setLayout(layout)

        AppGlobals.ProgramRunner().onMessage.connect(self.UpdateConsole)

        self._messages = []

    def UpdateConsole(self):
        messages = AppGlobals.ProgramRunner().GetMessages()
        delta = len(messages) - len(self._messages)

        for i in range(delta):
            messageItem = MessageItem()
            self._messages.append(messageItem)
            self._consoleLayout.addWidget(messageItem)

        for i in range(-delta):
            self._messages.pop().deleteLater()

        for i in range(len(messages)):
            message = messages[i]
            self._messages[i].SetMessage(message)
            self._messages[i].setProperty("IsEven", i % 2 == 0)


class MessageItem(QFrame):
    def __init__(self):
        super().__init__()

        self.nameLabel = QLabel("")
        self.programName = QLabel("")
        layout = QHBoxLayout()
        layout.addWidget(self.nameLabel)
        layout.addWidget(self.programName)

        self.setLayout(layout)

    def SetMessage(self, message: ProgramRunnerMessage):
        self.nameLabel.setText(message.text)
        self.programName.setText(message.programInstance.program.name)
