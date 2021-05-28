from PySide6.QtWidgets import QMenuBar
from PySide6.QtCore import Signal


class MenuBar(QMenuBar):
    showRigView = Signal()
    showProgramList = Signal()

    def __init__(self):
        super().__init__()

        self._fileMenu = self.addMenu("&File")

        self._fileMenu.addAction("New")
        self._fileMenu.addAction("Open...")
        self._recentMenu = self._fileMenu.addMenu("Open Recent")
        self._fileMenu.addAction("Save")
        self._fileMenu.addAction("Save As...")
        self._fileMenu.addAction("Close")
        self._fileMenu.addSeparator()
        self._fileMenu.addAction("Settings")
        self._fileMenu.addSeparator()
        self._fileMenu.addAction("Exit")
        self._fileMenu.setEnabled(False)

        self._editMenu = self.addMenu("&Edit")
        self._editMenu.addAction("Undo")
        self._editMenu.addAction("Redo")
        self._editMenu.addSeparator()
        self._editMenu.addAction("Cut")
        self._editMenu.addAction("Copy")
        self._editMenu.addAction("Paste")
        self._editMenu.addSeparator()
        self._editMenu.addAction("Select All")
        self._editMenu.setEnabled(False)

        self._viewMenu = self.addMenu("&View")
        self._zoomMenu = self._viewMenu.addMenu("Zoom")
        self._zoomMenu.addAction("In")
        self._zoomMenu.addAction("Out")
        self._zoomMenu.addAction("100%")
        self._zoomMenu.addAction("150%")
        self._zoomMenu.addAction("Fit All")
        self._viewMenu.addSeparator()
        self._viewMenu.addAction("Chip Programs").triggered.connect(self.showProgramList.emit)
        self._viewMenu.addAction("Rig").triggered.connect(self.showRigView.emit)
