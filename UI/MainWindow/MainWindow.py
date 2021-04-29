from PySide6.QtWidgets import QMainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.chipEditor = ChipEditor()

        self.setCentralWidget(self.chipEditor)