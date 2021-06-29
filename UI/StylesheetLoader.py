from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget
import typing
import os
import json
import re
from pathlib import Path


class StylesheetLoader:
    _instance = None

    @staticmethod
    def _GetInstance():
        if StylesheetLoader._instance is None:
            StylesheetLoader._instance = StylesheetLoader()
        return StylesheetLoader._instance

    @staticmethod
    def RegisterWidget(widget: QWidget):
        instance = StylesheetLoader._GetInstance()
        if instance.stylesheet is None:
            instance.ReloadSS()
        instance.widgetsList.append(widget)
        widget.setStyleSheet(instance.stylesheet)

    @staticmethod
    def UnregisterWidget(widget: QWidget):
        instance = StylesheetLoader._GetInstance()
        if widget in instance.widgetsList:
            instance.widgetsList.remove(widget)

    def __init__(self):
        self.widgetsList: typing.List[QWidget] = []

        self.updateTimer = QTimer(QApplication.topLevelWidgets()[0])
        self.updateTimer.timeout.connect(self.TimerUpdate)
        self.updateTimer.start(1000)

        self.stylesheetsLastModifiedTime = {}
        self.variablesLastModifiedTime = None

        self.stylesheetDirectory = Path("UI/Stylesheets")
        self.variablesFilename = "UI/StyleVariables.json"

        self.stylesheet = None
        self.variables = None

        self.TimerUpdate()

    def TimerUpdate(self):
        files = self.stylesheetDirectory.iterdir()
        reload = False
        for file in files:
            modTime = os.path.getmtime(file)
            if file not in self.stylesheetsLastModifiedTime or self.stylesheetsLastModifiedTime[file] != modTime:
                reload = True
                self.stylesheetsLastModifiedTime[file] = modTime
                break

        variablesModifiedTime = os.path.getmtime(self.variablesFilename)
        if reload or variablesModifiedTime != self.variablesLastModifiedTime:
            self.ReloadSS()
            self.variablesLastModifiedTime = variablesModifiedTime

    def ReloadSS(self):
        self.stylesheet = ""
        for file in self.stylesheetDirectory.iterdir():
            f = open(file)
            self.stylesheet += f.read()
            f.close()

        f = open(self.variablesFilename)
        self.variables = json.loads(f.read())
        f.close()

        self.stylesheet = re.sub(r"@\w+", lambda x: self.variables[x.group(0)[1:]], self.stylesheet)

        self.widgetsList: typing.List[QWidget] = [widget for widget in self.widgetsList if widget]
        for widget in self.widgetsList:
            widget.setStyleSheet(self.stylesheet)
            widget.setStyle(widget.style())
