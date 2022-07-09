from Data.Rig import Rig
from Data.Chip import Chip
from typing import Optional
from pathlib import Path
from PySide6.QtGui import QCursor, QGuiApplication


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
        if UIMaster.Instance().currentCursorShape != cursorShape:
            if cursorShape is not None:
                if UIMaster.Instance().currentCursorShape is None:
                    QGuiApplication.setOverrideCursor(QCursor(cursorShape))
                else:
                    QGuiApplication.changeOverrideCursor(QCursor(cursorShape))
            else:
                QGuiApplication.restoreOverrideCursor()
            UIMaster.Instance().currentCursorShape = cursorShape
