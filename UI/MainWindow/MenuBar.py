from PySide6.QtWidgets import QMenuBar
from PySide6.QtGui import QKeySequence
from PySide6.QtCore import Signal


class MenuBar(QMenuBar):
    showRigView = Signal()
    showProgramList = Signal()
    save = Signal()
    saveAs = Signal()
    new = Signal()
    open = Signal()
    exit = Signal()
    zoomToFit = Signal()

    def __init__(self):
        super().__init__()

        self._fileMenu = self.addMenu("&File")

        newAction = self._fileMenu.addAction("New")
        newAction.triggered.connect(self.new.emit)
        newAction.setShortcut(QKeySequence("Ctrl+N"))
        openAction = self._fileMenu.addAction("Open...")
        openAction.triggered.connect(self.open.emit)
        openAction.setShortcut(QKeySequence("Ctrl+O"))

        saveAction = self._fileMenu.addAction("Save")
        saveAction.triggered.connect(self.save.emit)
        saveAction.setShortcut(QKeySequence("Ctrl+S"))

        saveAsAction = self._fileMenu.addAction("Save As...")
        saveAsAction.triggered.connect(self.saveAs.emit)
        saveAsAction.setShortcut(QKeySequence("Ctrl+Shift+S"))

        exitAction = self._fileMenu.addAction("Exit")
        exitAction.triggered.connect(self.exit.emit)

        self._editMenu = self.addMenu("&Edit")
        # self._editMenu.addAction("Undo")
        # self._editMenu.addAction("Redo")
        # self._editMenu.addSeparator()
        # self._editMenu.addAction("Cut")
        # self._editMenu.addAction("Copy")
        # self._editMenu.addAction("Paste")
        # self._editMenu.addSeparator()
        # self._editMenu.addAction("Select All")

        self._viewMenu = self.addMenu("&View")
        self._zoomMenu = self._viewMenu.addMenu("Zoom")
        # self._zoomMenu.addAction("In")
        # self._zoomMenu.addAction("Out")
        # self._zoomMenu.addAction("100%")
        # self._zoomMenu.addAction("150%")
        self._zoomMenu.addAction("Fit All").triggered.connect(self.zoomToFit.emit)
        # self._viewMenu.addSeparator()
        self._viewMenu.addAction("Chip Programs").triggered.connect(self.showProgramList.emit)
        self._viewMenu.addAction("Rig").triggered.connect(self.showRigView.emit)
