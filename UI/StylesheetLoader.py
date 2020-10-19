from PySide2.QtCore import *
from PySide2.QtWidgets import *
from shiboken2 import *


class StylesheetLoader:
    _instance = None

    @staticmethod
    def GetInstance():
        if StylesheetLoader._instance is None:
            StylesheetLoader._instance = StylesheetLoader()
        return StylesheetLoader._instance

    def RegisterWidget(self, widget: QWidget):
        if self.stylesheet is None:
            self.ReloadSS()
        self.widgetsList.append(widget)
        widget.setStyleSheet(self.stylesheet)

    def __init__(self):
        self.widgetsList: typing.List[QWidget] = []

        self.updateTimer = QTimer(QApplication.topLevelWidgets()[0])
        self.updateTimer.timeout.connect(self.TimerUpdate)
        self.updateTimer.start(1000)

        self.lastModifiedTime = None

        self.scriptFilename = "Assets/STYLESHEET.css"

        self.stylesheet = None

    def TimerUpdate(self):
        currentModifiedTime = os.path.getmtime(self.scriptFilename)
        if currentModifiedTime != self.lastModifiedTime:
            self.ReloadSS()
            self.lastModifiedTime = currentModifiedTime

    def ReloadSS(self):
        f = open(self.scriptFilename)
        self.stylesheet = f.read()

        self.widgetsList: typing.List[QWidget] = [widget for widget in self.widgetsList if isValid(widget)]
        for widget in self.widgetsList:
            widget.setStyleSheet(self.stylesheet)
