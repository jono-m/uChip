from PySide6.QtWidgets import QMainWindow, QDockWidget, QTabWidget, QWidget, QMenuBar, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence
from UI.ChipView import ChipView
from UI.RigView import RigView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.chipEditor = ChipView()

        self.setCentralWidget(self.chipEditor)
        self.setWindowIcon(QIcon("Assets/Images/icon.png"))

        self.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.TabPosition.North)

        self.resize(1600, 900)

        self.rigView = RigView()
        self.dockPositions = {self.rigView: Qt.RightDockWidgetArea}

        self.BuildMenu()

        self.ShowWidget(self.rigView)

    def BuildMenu(self):
        menuBar = QMenuBar()

        fileMenu = menuBar.addMenu("&File")
        newAction = fileMenu.addAction("New")
        newAction.setShortcut(QKeySequence("Ctrl+N"))
        openAction = fileMenu.addAction("Open...")
        openAction.setShortcut(QKeySequence("Ctrl+O"))

        saveAction = fileMenu.addAction("Save")
        saveAction.setShortcut(QKeySequence("Ctrl+S"))

        saveAsAction = fileMenu.addAction("Save As...")
        saveAsAction.setShortcut(QKeySequence("Ctrl+Shift+S"))

        exitAction = fileMenu.addAction("Exit")

        viewMenu = menuBar.addMenu("View")
        viewRigAction = viewMenu.addAction("Rig")
        viewRigAction.triggered.connect(lambda: self.ShowWidget(self.rigView))

        self.setMenuBar(menuBar)

    def ShowWidget(self, widget: QWidget):
        if widget.isVisible():
            return

        dock = QDockWidget()
        dock.setWindowTitle(widget.objectName())
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        dock.setWidget(widget)
        dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self.addDockWidget(self.dockPositions[widget], dock)
