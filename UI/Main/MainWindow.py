import typing
import dill
from pathlib import Path

from PySide6.QtWidgets import QMainWindow, QFrame, QFileDialog, QVBoxLayout, QMessageBox
from PySide6.QtGui import QIcon, QCloseEvent
from PySide6.QtCore import QSize, QPoint, QTimer

from UI.StylesheetLoader import StylesheetLoader
from UI.Main.MenuBar import MenuBar, MenuHandler
from UI.Main.NewDialog import NewDialog, NewHandler
from ProjectSystem.ProjectTypes import ProjectType
from UI.ProjectTabs.ProjectTabArea import ProjectTabArea

from ProjectSystem.Project import ProjectFileError


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        StylesheetLoader.RegisterWidget(self)

        container = QFrame()
        layout = QVBoxLayout()
        container.setLayout(layout)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(container)
        icon = QIcon("Images/icon.png")
        self.setWindowIcon(icon)

        self.projectWindow = ProjectTabArea()
        layout.addWidget(self.projectWindow)

        menuHandler = MenuHandler()
        menuHandler.OnNew = self.PromptNew
        menuHandler.OnOpen = self.BrowseOpen
        menuHandler.OnOpenRecent = self.DoOpenRecent
        menuHandler.OnSave = lambda: self.projectWindow.GetActiveTab().Save()
        menuHandler.OnSaveAs = lambda: self.projectWindow.GetActiveTab().SaveAs(NewDialog.BrowseForLocation(self))
        menuHandler.OnClose = lambda: self.projectWindow.CloseRequest(self.projectWindow.GetActiveTab())
        self._menuBar = MenuBar(self, menuHandler)
        self.setMenuBar(self._menuBar)

        self._recentFiles = []

        self.ReloadSettings()

        self.LoadRecentFilesList()

        self._menuUpdateTimer = QTimer(self)
        self._menuUpdateTimer.timeout.connect(self.UpdateMenu)
        self._menuUpdateTimer.start(500)

    def PromptNew(self):
        newHandler = NewHandler()
        newHandler.OnNewRequest = self.DoNew

        NewDialog(self, newHandler).exec_()

    def UpdateMenu(self):
        activeTab = self.projectWindow.GetActiveTab()
        if activeTab:
            self._menuBar.SetState(activeTab.HasBeenModified(), True, True)
        else:
            self._menuBar.SetState(False, False, False)

    def DoNew(self, path: Path):
        project = ProjectType.TypeFromPath(path).CreateProject(path)
        project.Close()
        self.DoOpen(path)

    def LoadRecentFilesList(self):
        if Path("recentFiles.pkl").exists():
            file = open("recentFiles.pkl", "rb")
            self._recentFiles = dill.load(file)
            file.close()
        else:
            self._recentFiles = []
        self._recentFiles = [recentFile for recentFile in self._recentFiles[:10] if Path(recentFile).exists()]
        self._menuBar.PopulateRecentList(self._recentFiles)

    def SaveRecentFilesList(self):
        self._recentFiles = [recentFile for recentFile in self._recentFiles[:10] if Path(recentFile).exists()]
        file = open("recentFiles.pkl", "wb")
        dill.dump(self._recentFiles, file)
        file.close()
        self.LoadRecentFilesList()

    def BrowseOpen(self):
        fileName = QFileDialog.getOpenFileName(self, filter=ProjectType.allFilter())[0]
        if fileName == "":
            return
        else:
            self.DoOpen(Path(fileName))

    def DoOpen(self, path: Path):
        if not path.exists():
            QMessageBox.critical(self, "File Error", "Could not find file " + str(path.absolute()))
        elif ProjectType.TypeFromPath(path) is None:
            QMessageBox.critical(self, "File Error", "File type '" + path.suffix + "' not recognized.")
        else:
            for tab in self.projectWindow.GetTabs():
                if tab.GetPath() == path:
                    self.projectWindow.SelectTab(tab)
                    return
            try:
                tab = ProjectType.TypeFromPath(path).OpenProjectInTab(path)
            except ProjectFileError as e:
                QMessageBox.critical(self, "File Error", str(e))
                return

            self.projectWindow.AddTab(tab)

            while path in self._recentFiles:
                self._recentFiles.remove(path)
            self._recentFiles.insert(0, path)

        self.SaveRecentFilesList()

    def DoOpenRecent(self, path: typing.Optional[str]):
        if path is None:
            self._recentFiles = []
            self.SaveRecentFilesList()
        else:
            self.DoOpen(Path(path))

    def SaveSettings(self):
        windowSettings = WindowSettings()
        windowSettings.maximized = self.isMaximized()
        windowSettings.position = self.pos()
        windowSettings.size = self.size()
        file = open("windowSettings.pkl", "wb")
        dill.dump(windowSettings, file)
        file.close()

    def ReloadSettings(self):
        if Path("windowSettings.pkl").exists():
            file = open("windowSettings.pkl", "rb")
            windowSettings = dill.load(file)
        else:
            windowSettings = WindowSettings()

        self.resize(windowSettings.size)
        self.move(windowSettings.position)
        if windowSettings.maximized:
            self.showMaximized()
        else:
            self.showNormal()

    def closeEvent(self, event: QCloseEvent):
        self.SaveSettings()


class WindowSettings:
    size = QSize(w=1000, h=1200)
    position = QPoint(100, 100)
    maximized = False
