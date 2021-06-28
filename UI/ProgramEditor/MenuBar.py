from PySide6.QtWidgets import QMenuBar
from PySide6.QtGui import QKeySequence
from PySide6.QtCore import Signal


class MenuBar(QMenuBar):
    newProgram = Signal()
    openProgram = Signal()
    saveProgram = Signal()
    saveProgramAs = Signal()
    closeProgram = Signal()

    def __init__(self):
        super().__init__()

        self._fileMenu = self.addMenu("&File")

        self._fileMenu.addAction("New").triggered.connect(self.newProgram.emit)
        self._fileMenu.addSeparator()
        self._fileMenu.addAction("Open...").triggered.connect(self.openProgram.emit)
        self._recentMenu = self._fileMenu.addMenu("Open Recent")
        self._fileMenu.addSeparator()
        saveAction = self._fileMenu.addAction("Save")
        saveAction.triggered.connect(self.saveProgram.emit)
        saveAction.setShortcut(QKeySequence("Ctrl+S"))
        self._fileMenu.addAction("Save As...").triggered.connect(self.saveProgramAs.emit)
        self._fileMenu.addSeparator()
        self._fileMenu.addAction("Close").triggered.connect(self.closeProgram.emit)
        self._fileMenu.addSeparator()
        self._fileMenu.addAction("Settings")
        self._fileMenu.addSeparator()
        self._fileMenu.addAction("Exit")

        self._editMenu = self.addMenu("&Edit")
        self._editMenu.addAction("Undo")
        self._editMenu.addAction("Redo")
        self._editMenu.addSeparator()
        self._editMenu.addAction("Cut")
        self._editMenu.addAction("Copy")
        self._editMenu.addAction("Paste")
        self._editMenu.addSeparator()
        self._editMenu.addAction("Select All")

        self._viewMenu = self.addMenu("&View")
