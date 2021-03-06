from PySide6.QtWidgets import QMainWindow, QDockWidget, QMessageBox, QFileDialog, QTabWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from UI.ChipEditor.ChipEditor import ChipEditor
from UI.ProgramViews.ProgramList import ProgramList, Program
from UI.StylesheetLoader import StylesheetLoader
from UI.MainWindow.MenuBar import MenuBar
from UI.RigViewer.RigViewer import RigViewer
from UI.AppGlobals import AppGlobals, Chip
from UI.ProgramEditor.ProgramEditorWindow import ProgramEditorWindow
from UI.MainWindow.ProgramRunnerWorker import ProgramRunnerWorker
from UI.ProgramViews.RunningProgramsList import RunningProgramsList
from UI.ProgramViews.ConsoleViewer import ConsoleViewer

from pathlib import Path


class MainWindow(QMainWindow):
    def __init__(self):

        super().__init__()

        AppGlobals.Instance().onChipDataModified.connect(self.UpdateTitle)
        AppGlobals.Instance().onChipOpened.connect(self.UpdateTitle)
        AppGlobals.Instance().onChipSaved.connect(self.UpdateTitle)

        StylesheetLoader.RegisterWidget(self)

        self.chipEditor = ChipEditor()

        self.setCentralWidget(self.chipEditor)
        self.setWindowIcon(QIcon("Assets/Images/icon.png"))

        self._rigViewer = RigViewer()
        self._editorWindow = ProgramEditorWindow()
        self._programList = ProgramList(self)
        self._programList.onProgramEditRequest.connect(self.EditProgram)
        self._runningProgramsList = RunningProgramsList()
        self._consoleView = ConsoleViewer()
        self._editorWindow.setVisible(False)

        menuBar = MenuBar()
        menuBar.new.connect(self.NewChip)
        menuBar.open.connect(self.OpenChip)
        menuBar.save.connect(self.SaveChip)
        menuBar.saveAs.connect(lambda: self.SaveChip(True))
        menuBar.exit.connect(self.close)
        menuBar.showRigView.connect(self.ShowRigWidget)
        menuBar.showProgramList.connect(self.ShowProgramList)
        menuBar.showRunningProgramsList.connect(self.ShowRunningProgramsList)
        menuBar.showConsole.connect(self.ShowConsole)
        menuBar.zoomToFit.connect(self.chipEditor.viewer.Recenter)

        self.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.TabPosition.North)

        self.updateWorker = ProgramRunnerWorker(self)

        self.setMenuBar(menuBar)
        self.ShowRigWidget()
        self.ShowProgramList()
        self.ShowProgramEditorWindow()
        self.ShowRunningProgramsList()
        self.ShowConsole()
        self._editorWindow.close()

        AppGlobals.OpenChip(Chip())

        rect = self.screen().availableGeometry()
        self.resize(rect.width() / 2, rect.height() - 35)
        self.move(rect.center().x(), 0)

    def NewChip(self):
        if self.CloseChip():
            AppGlobals.OpenChip(Chip())

    def OpenChip(self):
        filename, filterType = QFileDialog.getOpenFileName(self, "Browse for Chip",
                                                           filter="μChip Project File (*.ucc)")
        if filename:
            if not self.CloseChip():
                return
            AppGlobals.OpenChip(Chip.LoadFromFile(Path(filename)))

    def UpdateTitle(self):
        title = AppGlobals.Chip().path
        if title:
            title = title.stem
        else:
            title = "New Chip"
        if AppGlobals.Chip().modified:
            title += "*"
        title += " - μChip"
        self.setWindowTitle(title)

    def SaveChip(self, saveAs=False) -> bool:
        if saveAs or not AppGlobals.Chip().HasBeenSaved():

            filename, filterType = QFileDialog.getSaveFileName(self, "Save Chip",
                                                               filter="μChip Project File (*.ucc)")
            if filename:
                AppGlobals.Chip().SaveToFile(Path(filename))
                AppGlobals.Instance().onChipSaved.emit()
                return True
            return False
        else:
            AppGlobals.Chip().SaveToFile(AppGlobals.Chip().path)
            AppGlobals.Instance().onChipSaved.emit()
            return True

    def CloseChip(self) -> bool:
        if AppGlobals.ProgramRunner().runningPrograms:
            status = QMessageBox.question(self, "Confirm", "There is a program running. Are you sure you want to stop?")
            if status is not QMessageBox.Yes:
                return False
            AppGlobals.ProgramRunner().StopAll()

        if self._editorWindow.isVisible():
            if not self._editorWindow.RequestCloseAll():
                return False

        if AppGlobals.Chip().modified:
            ret = QMessageBox.warning(self, "Confirm",
                                      "The current chip project has been modified.\nDo you want to save changes?",
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
            if ret is QMessageBox.Save:
                if not self.SaveChip():
                    return False
            elif ret is QMessageBox.Cancel:
                return False

        return True

    def closeEvent(self, event):
        if not self.CloseChip():
            event.ignore()
            return
        self.updateWorker.terminate()
        AppGlobals.Rig().SaveDevices()
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
        dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
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

    def ShowRunningProgramsList(self):
        if self._runningProgramsList.isVisible():
            return

        dock = QDockWidget()
        dock.setWindowTitle("Running Programs")
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        dock.setWidget(self._runningProgramsList)
        dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def ShowConsole(self):
        if self._consoleView.isVisible():
            return

        dock = QDockWidget()
        dock.setWindowTitle("Console")
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        dock.setWidget(self._consoleView)
        dock.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def ShowProgramEditorWindow(self):
        self._editorWindow.setVisible(True)
        self._editorWindow.activateWindow()
        self._editorWindow.setFocus()
