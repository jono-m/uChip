from PySide6.QtWidgets import QMainWindow, QDockWidget, QMessageBox
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from UI.ChipEditor.ChipEditor import ChipEditor
from UI.ProgramViews.ProgramList import ProgramList, Program
from UI.StylesheetLoader import StylesheetLoader
from UI.MainWindow.MenuBar import MenuBar
from UI.RigViewer.RigViewer import RigViewer
from UI.AppGlobals import AppGlobals, Chip
from UI.ProgramEditor.ProgramEditorWindow import ProgramEditorWindow
from UI.MainWindow.ProgramRunnerWorker import ProgramRunnerWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        AppGlobals.Rig().AddMock(0, "Mock A")
        AppGlobals.Rig().AddMock(24, "Mock B")
        AppGlobals.Rig().AddMock(48, "Mock C")
        AppGlobals.OpenChip(Chip())

        StylesheetLoader.RegisterWidget(self)

        self.chipEditor = ChipEditor()

        self.setCentralWidget(self.chipEditor)

        self.resize(self.screen().size() / 2)
        self.move(self.screen().size().width() / 2, 0)

        self.setWindowTitle("uChip")
        self.setWindowIcon(QIcon("Images/UCIcon.png"))

        self._rigViewer = RigViewer()
        self._editorWindow = ProgramEditorWindow()
        self._programList = ProgramList(self)
        self._programList.onProgramEditRequest.connect(self.EditProgram)
        self._editorWindow.setVisible(False)

        menuBar = MenuBar()
        menuBar.showRigView.connect(self.ShowRigWidget)
        menuBar.showProgramList.connect(self.ShowProgramList)

        self.updateWorker = ProgramRunnerWorker(self)
        self.updateWorker.start()

        killTimer = QTimer(self)
        killTimer.timeout.connect(self.CheckForKill)
        killTimer.start(1000)

        self.setMenuBar(menuBar)
        self.ShowRigWidget()
        self.ShowProgramList()
        self.ShowProgramEditorWindow()
        self._editorWindow.close()

    def CheckForKill(self):
        if AppGlobals.ProgramRunner().GetTickDelta() > 2:
            self.updateWorker.terminate()
            self.updateWorker.wait()
            AppGlobals.ProgramRunner().StopAll()
            self.updateWorker.start()
            QMessageBox.critical(self, "Timeout", "Program timed out.")

    def closeEvent(self, event):
        if AppGlobals.ProgramRunner().runningPrograms:
            status = QMessageBox.question(self, "Confirm", "There is a program running. Are you sure you want to quit?")
            if status is not QMessageBox.Yes:
                event.ignore()
                return
        if self._editorWindow.isVisible():
            if not self._editorWindow.RequestCloseAll():
                event.ignore()
                return
        self.updateWorker.stop()
        super().closeEvent(event)

    def EditProgram(self, program: Program):
        self.ShowProgramEditorWindow()
        self._editorWindow.OpenProgram(program)

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

    def ShowProgramEditorWindow(self):
        self._editorWindow.setVisible(True)
        self._editorWindow.activateWindow()
        self._editorWindow.setFocus()
