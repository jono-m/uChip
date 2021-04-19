from PySide6.QtWidgets import QMenuBar
from PySide6.QtGui import QKeySequence, QAction
from pathlib import Path
import typing


class MenuHandler:
    def OnNew(self):
        print("New")

    def OnOpen(self):
        print("Open")

    def OnOpenRecent(self, filePath: Path):
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

        fileMenu = self.addMenu("File")

        newAction = fileMenu.addAction("New...")
        newAction.setShortcut(QKeySequence.New)
        newAction.triggered.connect(handler.OnNew)

        openAction = fileMenu.addAction("Open...")
        openAction.setShortcut(QKeySequence.Open)
        openAction.triggered.connect(handler.OnOpen)

        self._recentMenu = fileMenu.addMenu("Open Recent")
        self._recentMenu.triggered.connect(lambda action: handler.OnOpenRecent(Path(action.typeName())))

        saveAction = fileMenu.addAction("Save")
        saveAction.setShortcut(QKeySequence.Save)
        saveAction.triggered.connect(handler.OnSave)

        saveAsAction = fileMenu.addAction("Save As...")
        saveAsAction.setShortcut(QKeySequence.SaveAs)
        saveAsAction.triggered.connect(handler.OnSaveAs)

        closeAction = fileMenu.addAction("Close")
        closeAction.setShortcut(QKeySequence.Close)
        closeAction.triggered.connect(handler.OnClose)

        exitAction = fileMenu.addAction("Exit")
        exitAction.setShortcut(QKeySequence.Quit)
        exitAction.triggered.connect(handler.OnExit)

        helpMenu = self.addMenu("Help")
        aboutAction = helpMenu.addAction("About...")
        aboutAction.triggered.connect(handler.OnAbout)

    def PopulateRecentList(self, paths: typing.List[Path]):
        self._recentMenu.clear()
        for path in paths:
            self._recentMenu.addAction(str(path.resolve()))
