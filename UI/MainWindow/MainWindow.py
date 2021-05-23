from PySide6.QtWidgets import QMainWindow
from UI.ChipEditor.ChipEditor import ChipEditor
from UI.StylesheetLoader import StylesheetLoader


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        StylesheetLoader.RegisterWidget(self)

        self.chipEditor = ChipEditor()

        self.setCentralWidget(self.chipEditor)

        self.resize(self.screen().size() / 2)
        self.move(self.screen().size().width() / 2, 0)
