from PySide6.QtWidgets import QMenuBar
from PySide6.QtGui import QKeySequence
from PySide6.QtCore import Signal


class MenuBar(QMenuBar):
    saveProgram = Signal()
    closeProgram = Signal()
    exportProgram = Signal()

    def __init__(self):
        super().__init__()

        self._fileMenu = self.addMenu("&File")
        saveAction = self._fileMenu.addAction("Save")
        saveAction.triggered.connect(self.saveProgram.emit)
        saveAction.setShortcut(QKeySequence("Ctrl+S"))
        self._fileMenu.addAction("Export").triggered.connect(self.exportProgram.emit)
        self._fileMenu.addAction("Close").triggered.connect(self.closeProgram.emit)
