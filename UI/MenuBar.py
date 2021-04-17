from PySide6.QtWidgets import *
from PySide6.QtGui import *


class MenuBar(QMenuBar):
    def __init__(self, parent):
        super().__init__(parent)

        fileMenu = self.addMenu("File")

        newMenu = fileMenu.addMenu("New...")

        newChipProjectAction = QAction("Chip Project")
        newBlockGraphAction = QAction("Block Graph Project")
        newBlockScriptAction = QAction("Block Script Project")

        newMenu.addActions([newChipProjectAction, newBlockGraphAction, newBlockScriptAction])
