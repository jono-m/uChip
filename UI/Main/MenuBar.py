from PySide6.QtWidgets import QMenuBar
from PySide6.QtGui import QKeySequence, QAction
from pathlib import Path
import typing


class MenuHandler:
    def OnNew(self):
        print("New")

    def OnOpen(self):
        print("Open")

    def OnOpenRecent(self, filePath: typing.Optional[str]):
        if filePath is not None:
            print("Open " + str(filePath.resolve()))

    def OnSave(self):
        print("Save")

    def OnSaveAs(self):
        print("Save As")

    def OnClose(self):
        print("On Close")

    def OnExit(self):
        print("Exit")

    def OnAbout(self):
        print("About")


class MenuBar(QMenuBar):
    def __init__(self, parent, handler: typing.Optional[MenuHandler] = MenuHandler()):
        super().__init__(parent)

        self._handler = handler
        fileMenu = self.addMenu("File")

        newAction = fileMenu.addAction("New...")
        newAction.setShortcut(QKeySequence.New)
        newAction.triggered.connect(handler.OnNew)

        openAction = fileMenu.addAction("Open...")
        openAction.setShortcut(QKeySequence.Open)
        openAction.triggered.connect(handler.OnOpen)

        self._recentMenu = fileMenu.addMenu("Open Recent")
        self._recentMenu.triggered.connect(self.OnOpenRecent)

        self._saveAction = fileMenu.addAction("Save")
        self._saveAction.setShortcut(QKeySequence.Save)
        self._saveAction.triggered.connect(handler.OnSave)

        self._saveAsAction = fileMenu.addAction("Save As...")
        self._saveAsAction.setShortcut(QKeySequence.SaveAs)
        self._saveAsAction.triggered.connect(handler.OnSaveAs)

        self._closeAction = fileMenu.addAction("Close")
        self._closeAction.setShortcut(QKeySequence.Close)
        self._closeAction.triggered.connect(handler.OnClose)

        exitAction = fileMenu.addAction("Exit")
        exitAction.setShortcut(QKeySequence.Quit)
        exitAction.triggered.connect(handler.OnExit)

        helpMenu = self.addMenu("Help")
        aboutAction = helpMenu.addAction("About...")
        aboutAction.triggered.connect(handler.OnAbout)

    def PopulateRecentList(self, paths: typing.List[Path]):
        self._recentMenu.clear()
        for path in paths:
            self._recentMenu.addAction(str(path.absolute().resolve()))
        self._recentMenu.addAction("Clear Recent Files")

    def OnOpenRecent(self, action):
        if action.text() == "Clear Recent Files":
            self._handler.OnOpenRecent(None)
        else:
            self._handler.OnOpenRecent(action.text())

    def SetState(self, saveEnable: bool, saveAsEnable: bool, closeEnable):
        self._saveAction.setEnabled(saveEnable)
        self._saveAsAction.setEnabled(saveAsEnable)
        self._closeAction.setEnabled(closeEnable)
