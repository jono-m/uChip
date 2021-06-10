from typing import List

from PySide6.QtWidgets import QTabWidget, QWidget, QMessageBox, QVBoxLayout, QMainWindow
from UI.ProgramEditor.ProgramEditorTab import ProgramEditorTab, Program
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from UI.AppGlobals import AppGlobals
from UI.StylesheetLoader import StylesheetLoader
from UI.ProgramEditor.MenuBar import MenuBar


class ProgramEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        StylesheetLoader.RegisterWidget(self)
        self.setWindowIcon(QIcon("Images/UCIcon.png"))

        centralLayout = QVBoxLayout()
        centralWidget = QWidget()
        centralWidget.setLayout(centralLayout)
        self.setCentralWidget(centralWidget)

        self._tabWidget = QTabWidget()
        centralLayout.addWidget(self._tabWidget)

        menuBar = MenuBar()
        self.setMenuBar(menuBar)

        menuBar.saveProgram.connect(lambda: self._tabWidget.currentWidget().SaveProgram())
        menuBar.closeProgram.connect(lambda: self.RequestCloseTab(self._tabWidget.currentIndex()))

        self._tabWidget.tabCloseRequested.connect(self.RequestCloseTab)
        self._tabWidget.setTabsClosable(True)

        timer = QTimer(self)
        timer.timeout.connect(self.CheckPrograms)
        timer.start(30)

    def OpenProgram(self, program: Program):
        for tab in self.tabs():
            if tab.program is program:
                self._tabWidget.setCurrentWidget(tab)
                return
        newTab = ProgramEditorTab(program)
        self._tabWidget.addTab(newTab, program.name)

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

    def CheckPrograms(self):
        modified = False
        for tab in self.tabs():
            title = tab.program.name
            if tab.modified:
                modified = True
                title += "*"
            self._tabWidget.setTabText(self._tabWidget.indexOf(tab), title)
            if tab.program not in AppGlobals.Chip().programs:
                self.deleteLater()

        current: ProgramEditorTab = self._tabWidget.currentWidget()
        if current:
            title = current.program.name
            if modified:
                title += " *"
            title += " | uChip Program Editor"
            self.setWindowTitle(title)
