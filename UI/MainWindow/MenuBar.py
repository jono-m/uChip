from PySide2.QtWidgets import *
from PySide2.QtGui import *
from PySide2.QtCore import *
from Util import *


class MenuBar(QFrame):
    def __init__(self):
        super().__init__()
        self.OnNewChip = Event()
        self.OnNewLB = Event()
        self.OnOpen = Event()
        self.OnSave = Event()
        self.OnSaveAs = Event()

        self.menuBar = QMenuBar()
        self.menuBar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        fileMenu = self.menuBar.addMenu("&File")
        newChipAction = QAction(QIcon("Assets/UCIcon.png"), "New Chip", self)
        newChipAction.setShortcut(Qt.CTRL + Qt.Key_N)
        newChipAction.triggered.connect(self.OnNewChip.Invoke)
        newLBAction = QAction(QIcon("Assets/LBIcon.png"), "New Logic Block", self)
        newLBAction.triggered.connect(self.OnNewLB.Invoke)
        newLBAction.setShortcut(Qt.CTRL + Qt.SHIFT + Qt.Key_N)
        openAction = QAction("Open...", self)
        openAction.setShortcut(Qt.CTRL + Qt.Key_O)
        openAction.triggered.connect(self.OnOpen.Invoke)
        saveAction = QAction("Save", self)
        saveAction.setShortcut(Qt.CTRL + Qt.Key_S)
        saveAction.triggered.connect(self.OnSave.Invoke)
        saveAsAction = QAction("Save As...", self)
        saveAsAction.setShortcut(Qt.CTRL + Qt.SHIFT + Qt.Key_S)
        saveAsAction.triggered.connect(self.OnSaveAs.Invoke)

        fileMenu.addAction(newChipAction)
        fileMenu.addAction(newLBAction)
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveAsAction)

        editMenu = self.menuBar.addMenu("&Edit")
        viewMenu = self.menuBar.addMenu("&View")
        helpMenu = self.menuBar.addMenu("&Help")

        self.setContentsMargins(0, 0, 0, 0)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)
        layout.addWidget(self.menuBar, alignment=Qt.AlignCenter)

    def SetIsProcedureRunning(self, isRunning):
        self.setEnabled(not isRunning)