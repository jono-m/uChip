import typing
import os
from PySide2.QtCore import *
from PySide2.QtWidgets import *


class StylesheetLoader:
    _instance = None

    @staticmethod
    def GetInstance():
        if StylesheetLoader._instance is None:
            StylesheetLoader._instance = StylesheetLoader()
        return StylesheetLoader._instance

    def RegisterWidget(self, widget: QWidget):
        self.widgetsList.append(widget)

    def __init__(self):
        self.widgetsList: typing.List[QWidget] = []

        self.updateTimer = QTimer(QApplication.topLevelWidgets()[0])
        self.updateTimer.timeout.connect(self.TimerUpdate)
        self.updateTimer.start(1000)

        self.lastModifiedTime = None

        self.scriptFilename = "UI/STYLESHEET.css"

    def TimerUpdate(self):
        currentModifiedTime = os.path.getmtime(self.scriptFilename)
        if currentModifiedTime != self.lastModifiedTime:
            self.ReloadSS()
            self.lastModifiedTime = currentModifiedTime

    def ReloadSS(self):
        f = open(self.scriptFilename)
        stylesheet = f.read()

        for widget in self.widgetsList:
            widget.setStyleSheet(stylesheet)
