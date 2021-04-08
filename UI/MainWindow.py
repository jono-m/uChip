from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from UI.StylesheetLoader import StylesheetLoader
from RigSystem.Rig import Rig
import dill
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        StylesheetLoader.GetInstance().RegisterWidget(self)

        container = QFrame()
        container.setObjectName("Container")
        container.setFrameShape(QFrame.NoFrame)
        self.setCentralWidget(container)

        icon = QIcon("Images/icon.png")
        self.setWindowIcon(icon)

        self.rig = Rig()

    def SaveSettings(self):
        windowSettings = WindowSettings()
        windowSettings.maximized = self.isMaximized()
        windowSettings.position = self.pos()
        windowSettings.size = self.size()
        file = open("windowSettings.pkl", "wb")
        dill.dump(windowSettings, file)
        file.close()

    def ReloadSettings(self):
        windowSettings = WindowSettings()
        if os.path.exists("windowSettings.pkl"):
            file = open("windowSettings.pkl", "rb")
            windowSettings = dill.load(file)

        self.resize(windowSettings.size)
        self.move(windowSettings.position)
        if windowSettings.maximized:
            self.showMaximized()
        else:
            self.showNormal()

    def closeEvent(self, event: QCloseEvent):
        self.SaveSettings()


class WindowSettings:
    size = QSize(1000, 1200)
    position = QPoint(100, 100)
    maximized = False
