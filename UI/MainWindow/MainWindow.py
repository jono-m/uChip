from PySide6.QtWidgets import QMainWindow
from UI.ChipEditor.ChipEditor import ChipEditor


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.chipEditor = ChipEditor()

        self.setCentralWidget(self.chipEditor)
