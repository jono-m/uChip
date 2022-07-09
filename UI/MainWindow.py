import pathlib

from PySide6.QtWidgets import QMainWindow, QDockWidget, QTabWidget, QWidget, QMenuBar, QFileDialog, \
    QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence
from UI.ChipView import ChipView
from UI.RigView import RigView
from UI.UIMaster import UIMaster
from Data.FileIO import SaveObject, LoadObject
from Data.Chip import Chip


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

        self.NewChip()

    def NewChip(self):
        if not self.PromptCloseChip():
            return
        UIMaster.Instance().currentChip = Chip()
        self.chipEditor.CloseChip()
        self.chipEditor.OpenChip()
        UIMaster.Instance().modified = False

    def SaveChip(self, saveAs: bool):
        if saveAs or UIMaster.Instance().currentChipPath is None:
            d = QFileDialog.getSaveFileName(self, "Save Path", filter="uChip Project (*.ucp)")
            if d[0]:
                UIMaster.Instance().currentChipPath = pathlib.Path(d[0])
            else:
                return False
        SaveObject(UIMaster.Instance().currentChip, UIMaster.Instance().currentChipPath)
        UIMaster.Instance().modified = False
        return True

    def OpenChip(self):
        if not self.PromptCloseChip():
            return
        d = QFileDialog.getOpenFileName(self, "Open Chip", filter="uChip Project (*.ucp)")
        if d[0]:
            self.chipEditor.CloseChip()
            UIMaster.Instance().currentChipPath = pathlib.Path(d[0])
            UIMaster.Instance().currentChip = LoadObject(UIMaster.Instance().currentChipPath)
            self.chipEditor.OpenChip()
            UIMaster.Instance().modified = False
        else:
            return

    def PromptCloseChip(self):
        if UIMaster.Instance().modified:
            value = QMessageBox.critical(self, "Confirm Action",
                                         "This uChip project has been modified. Do you want to discard changes?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if value == QMessageBox.Cancel:
                return False
            elif value == QMessageBox.Save:
                return self.SaveChip(False)
        return True

    def closeEvent(self, event):
        if self.PromptCloseChip():
            super().closeEvent(event)
        else:
            event.ignore()

    def BuildMenu(self):
        menuBar = QMenuBar()

        fileMenu = menuBar.addMenu("&File")
        newAction = fileMenu.addAction("New")
        newAction.triggered.connect(self.NewChip)
        newAction.setShortcut(QKeySequence("Ctrl+N"))
        openAction = fileMenu.addAction("Open...")
        openAction.setShortcut(QKeySequence("Ctrl+O"))
        openAction.triggered.connect(self.OpenChip)

        saveAction = fileMenu.addAction("Save")
        saveAction.setShortcut(QKeySequence("Ctrl+S"))
        saveAction.triggered.connect(lambda: self.SaveChip(False))

        saveAsAction = fileMenu.addAction("Save As...")
        saveAsAction.setShortcut(QKeySequence("Ctrl+Shift+S"))
        saveAsAction.triggered.connect(lambda: self.SaveChip(True))

        exitAction = fileMenu.addAction("Exit")
        exitAction.triggered.connect(self.close)

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
