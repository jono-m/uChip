from typing import List

from PySide6.QtWidgets import QTabWidget, QMessageBox, QMainWindow, QSplitter, QFileDialog
from UI.ProgramEditor.ProgramEditorTab import ProgramEditorTab, Program
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from UI.StylesheetLoader import StylesheetLoader
from UI.ProgramEditor.MenuBar import MenuBar
from UI.ProgramEditor.Instructions import Instructions
from UI.AppGlobals import AppGlobals


class ProgramEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        AppGlobals.Instance().onChipAddRemove.connect(self.UpdateDisplay)
        StylesheetLoader.RegisterWidget(self)
        self.setWindowIcon(QIcon("Assets/Images/icon.png"))
        self._tabWidget = QTabWidget()

        self.setCentralWidget(self._tabWidget)

        menuBar = MenuBar()
        self.setMenuBar(menuBar)

        menuBar.saveProgram.connect(self.SaveProgram)
        menuBar.exportProgram.connect(self.ExportProgram)
        menuBar.closeProgram.connect(lambda: self.RequestCloseTab(self._tabWidget.currentIndex()))
        menuBar.helpAction.connect(self.ShowInstructions)

        self._instructionsWindow = Instructions(self)
        self._instructionsWindow.setVisible(False)

        self._tabWidget.tabCloseRequested.connect(self.RequestCloseTab)
        self._tabWidget.currentChanged.connect(self.UpdateDisplay)
        self._tabWidget.setTabsClosable(True)

    def SaveProgram(self):
        self._tabWidget.currentWidget().SaveProgram()
        self.UpdateDisplay()

    def ExportProgram(self):
        filename, filterType = QFileDialog.getSaveFileName(self, "Export Program", filter="μChip Program File (*.ucp)")
        if filename:
            self._tabWidget.currentWidget().ExportProgram(filename)

    def ShowInstructions(self):
        self._instructionsWindow.show()

    def OpenProgram(self, program: Program):
        for tab in self.tabs():
            if tab.program is program:
                self._tabWidget.setCurrentWidget(tab)
                return
        newTab = ProgramEditorTab(program)
        newTab.onModified.connect(self.UpdateDisplay)
        self._tabWidget.addTab(newTab, program.name)
        self._tabWidget.setCurrentIndex(self._tabWidget.count() - 1)

    def RequestCloseTab(self, index):
        tab: ProgramEditorTab = self._tabWidget.widget(index)
        self._tabWidget.setCurrentWidget(tab)
        if tab.modified:
            ret = QMessageBox.warning(self, "Confirm",
                                      "'" + tab.program.name + "' has been modified.\nDo you want to save changes?",
                                      QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
            if ret is QMessageBox.Save:
                tab.SaveProgram()
            elif ret is QMessageBox.Cancel:
                return False
        self._tabWidget.removeTab(index)
        if not self._tabWidget.count():
            self.close()
        return True

    def closeEvent(self, event) -> None:
        if not self.RequestCloseAll():
            event.ignore()

    def RequestCloseAll(self):
        while self._tabWidget.count():
            if not self.RequestCloseTab(0):
                return False
        return True

    def tabs(self) -> List[ProgramEditorTab]:
        return [self._tabWidget.widget(i) for i in range(self._tabWidget.count())]

    def UpdateDisplay(self):
        modified = False
        for tab in self.tabs():
            title = tab.program.name
            if tab.modified:
                modified = True
                title += "*"
            self._tabWidget.setTabText(self._tabWidget.indexOf(tab), title)

        current: ProgramEditorTab = self._tabWidget.currentWidget()
        if current:
            title = current.program.name
            if modified:
                title += " *"
            title += " | μChip Program Editor"
            self.setWindowTitle(title)
        else:
            self.close()
