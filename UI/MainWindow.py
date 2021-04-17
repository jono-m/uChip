from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from UI.StylesheetLoader import StylesheetLoader
import dill
from pathlib import Path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        StylesheetLoader.GetInstance().RegisterWidget(self)

        container = QFrame()
        self.setCentralWidget(container)

        icon = QIcon("Images/icon.png")
        self.setWindowIcon(icon)

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
