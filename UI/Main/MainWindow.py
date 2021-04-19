from PySide6.QtWidgets import QMainWindow, QFrame, QFileDialog, QVBoxLayout, QLabel
from PySide6.QtGui import QIcon, QCloseEvent
from PySide6.QtCore import QSize, QPoint
from UI.StylesheetLoader import StylesheetLoader
from UI.Main.MenuBar import MenuBar, MenuHandler
from UI.Main.NewDialog import NewDialog, ProjectType
from UI.ProjectWindow.ProjectWindow import ProjectWindow
import dill
from pathlib import Path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        StylesheetLoader.GetInstance().RegisterWidget(self)

        container = QFrame()
        layout = QVBoxLayout()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.projectWindow = ProjectWindow()
        layout.addWidget(self.projectWindow)

        menuHandler = MenuHandler()
        # menuHandler.OnNew = lambda: NewDialog(self).exec_()
        menuHandler.OnNew = lambda: self.projectWindow.AddTab(QLabel("Hello!"), "Test")
        menuHandler.OnOpen = lambda: self.DoOpen(
            QFileDialog.getOpenFileName(self, filter=ProjectType.allFilter()))
        menuBar = MenuBar(self, menuHandler)
        self.setMenuBar(menuBar)

        icon = QIcon("Images/icon.png")
        self.setWindowIcon(icon)

        self.ReloadSettings()

    def DoOpen(self, result):
        filenameOpen = Path(result[0])
        newType = [newType for newType in ProjectType if (newType.fileExtension()) == filenameOpen.suffix]
        print(str(newType) + "-" + str(filenameOpen.absolute().resolve()))

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
