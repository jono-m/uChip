from typing import Dict
from PySide6.QtWidgets import QMainWindow, QDockWidget, QTabWidget, QWidget, QMenuBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence
from UI.ChipView import ChipView
from UI.StylesheetLoader import StylesheetLoader
from UI.RigView import RigView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        StylesheetLoader.RegisterWidget(self)

        self.chipEditor = ChipView()

        self.setCentralWidget(self.chipEditor)
        self.setWindowIcon(QIcon("Assets/Images/icon.png"))

        self._rigView = RigView()
        self.dockPositions: Dict[QWidget, Qt.DockWidgetArea] = {
            self._rigView: Qt.BottomDockWidgetArea}

        self.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.TabPosition.North)

        self.BuildMenu()

    def BuildMenu(self):
        menuBar = QMenuBar()

        fileMenu = menuBar.addMenu("&File")
        newAction = fileMenu.addAction("New")
        newAction.triggered.connect(self.NewChip)
        newAction.setShortcut(QKeySequence("Ctrl+N"))
        openAction = fileMenu.addAction("Open...")
        openAction.triggered.connect(self.OpenChip)
        openAction.setShortcut(QKeySequence("Ctrl+O"))

        saveAction = fileMenu.addAction("Save")
        saveAction.triggered.connect(self.SaveChip)
        saveAction.setShortcut(QKeySequence("Ctrl+S"))

        saveAsAction = fileMenu.addAction("Save As...")
        saveAsAction.triggered.connect(self.SaveChipAs)
        saveAsAction.setShortcut(QKeySequence("Ctrl+Shift+S"))

        exitAction = fileMenu.addAction("Exit")
        exitAction.triggered.connect(self.CloseAll)

        viewMenu = menuBar.addMenu("&View")
        viewMenu.addAction("Rig").triggered.connect(lambda: self.ShowWidget(self._rigView))

        self.setMenuBar(menuBar)

    def ShowWidget(self, widget: QWidget):
        if widget.isVisible():
            return

        dock = QDockWidget()
        dock.setWindowTitle(widget.objectName())
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        dock.setWidget(widget)
        dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self.addDockWidget(self.dockPositions[widget], dock)
