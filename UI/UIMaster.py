from Data.Rig import Rig
from Data.Chip import Chip
from typing import Optional
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtCore import Qt


class UIMaster:
    _instance = None

    def __init__(self):
        super().__init__()
        self.rig = Rig()
        self.currentChip = Chip()
        self.modified = False
        self.currentChipPath: Optional[Path] = None
        self.currentCursorShape: Optional[QCursor] = None

    @staticmethod
    def Instance():
        if UIMaster._instance is None:
            UIMaster._instance = UIMaster()
        return UIMaster._instance

    @staticmethod
    def SetCursor(cursorShape: Optional[QCursor]):
        QGuiApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        return
        if UIMaster.Instance().currentCursorShape != cursorShape:
            UIMaster.Instance().currentCursorShape = cursorShape
            if cursorShape is not None:
                w.setCursor(cursorShape)
            else:
                w.unsetCursor()
