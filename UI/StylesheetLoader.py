from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget
import typing
import os


class StylesheetLoader:
    _instance = None

    @staticmethod
    def GetInstance():
        if StylesheetLoader._instance is None:
            StylesheetLoader._instance = StylesheetLoader()
        return StylesheetLoader._instance

    @staticmethod
    def RegisterWidget(widget: QWidget):
        instance = StylesheetLoader.GetInstance()
        if instance.stylesheet is None:
            instance.ReloadSS()
        instance.widgetsList.append(widget)
        widget.setStyleSheet(instance.stylesheet)

    def __init__(self):
        self.widgetsList: typing.List[QWidget] = []

        self.updateTimer = QTimer(QApplication.topLevelWidgets()[0])
        self.updateTimer.timeout.connect(self.TimerUpdate)
        self.updateTimer.start(1000)

        self.lastModifiedTime = None

        self.scriptFilename = "UI/STYLESHEET.css"

        self.stylesheet = None

    def TimerUpdate(self):
        currentModifiedTime = os.path.getmtime(self.scriptFilename)
        if currentModifiedTime != self.lastModifiedTime:
            self.ReloadSS()
            self.lastModifiedTime = currentModifiedTime

    def ReloadSS(self):
        f = open(self.scriptFilename)
        self.stylesheet = f.read()

        self.widgetsList: typing.List[QWidget] = [widget for widget in self.widgetsList if widget]
        for widget in self.widgetsList:
            widget.setStyleSheet(self.stylesheet)
