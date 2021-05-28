from PySide6.QtWidgets import QMainWindow, QDockWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from UI.ChipEditor.ChipEditor import ChipEditor
from UI.ProgramEditor.ProgramList import ProgramList
from UI.StylesheetLoader import StylesheetLoader
from UI.MainWindow.MenuBar import MenuBar
from UI.RigViewer.RigViewer import RigViewer
from UI.AppGlobals import AppGlobals, Chip


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        StylesheetLoader.RegisterWidget(self)

        self.chipEditor = ChipEditor()

        self.setCentralWidget(self.chipEditor)

        self.resize(self.screen().size() / 2)
        self.move(self.screen().size().width() / 2, 0)

        self.setWindowTitle("uChip")
        self.setWindowIcon(QIcon("Images/UCIcon.png"))

        AppGlobals.Rig().AddMock(0, "Mock A")
        AppGlobals.Rig().AddMock(24, "Mock B")
        AppGlobals.Rig().AddMock(48, "Mock C")
        AppGlobals.OpenChip(Chip())

        self._rigViewer = RigViewer()
        self._programList = ProgramList(self)

        menuBar = MenuBar()
        menuBar.showRigView.connect(self.ShowRigWidget)
        menuBar.showProgramList.connect(self.ShowProgramList)
        self.setMenuBar(menuBar)
        self.ShowRigWidget()
        self.ShowProgramList()

    def ShowRigWidget(self):
        if self._rigViewer.isVisible():
            return

        dock = QDockWidget()
        dock.setWindowTitle("Rig")
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        dock.setWidget(self._rigViewer)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

    def ShowProgramList(self):
        if self._programList.isVisible():
            return

        dock = QDockWidget()
        dock.setWindowTitle("Programs")
        dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        dock.setWidget(self._programList)
        dock.setFeatures(QDockWidget.DockWidgetClosable)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
