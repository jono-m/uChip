import time

from Data.Rig import Rig
from Data.Chip import Chip, Program
from Data.ProgramCompilation import CompiledProgram, Recompile, Compile
from typing import Optional, List
from pathlib import Path
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QApplication


class UIMaster:
    _instance = None

    def __init__(self):
        super().__init__()
        self.topLevel = QApplication.topLevelWidgets()[0]
        self.compiledPrograms: List[CompiledProgram] = []
        self.rig = Rig()
        self.currentChip = Chip()
        self.modified = False
        self.currentChipPath: Optional[Path] = None
        self.currentCursorShape: Optional[QCursor] = None

    @staticmethod
    def Recompile(p: Program):
        match = UIMaster.GetCompiledProgram(p)
        if match is None:
            match = Compile(p, UIMaster.Instance().currentChip, UIMaster.Instance().rig,
                            UIMaster.Instance().compiledPrograms)
            match.lastScriptModifiedTime = p.path.stat().st_mtime
            UIMaster.Instance().compiledPrograms.append(match)
        else:
            Recompile(match, UIMaster.Instance().currentChip, UIMaster.Instance().rig,
                      UIMaster.Instance().compiledPrograms)
        match.lastScriptModifiedTime = p.path.stat().st_mtime
        match.lastScriptPath = p.path

    @staticmethod
    def GetCompiledProgram(p: Program):
        return next((x for x in UIMaster.Instance().compiledPrograms if x.program == p), None)

    @staticmethod
    def ShouldRecompile(p: Program):
        match = UIMaster.GetCompiledProgram(p)
        if match is None:
            return True
        if match.lastScriptPath != p.path or match.lastScriptModifiedTime < p.path.stat().st_mtime:
            return True
        return False

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
