from Data.Rig import Rig
from Data.Chip import Chip, Program
from Data.FileIO import SaveObject, LoadObject
import Data.ProgramCompilation as ProgramCompilation
from typing import Optional, List, Dict
from pathlib import Path
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QApplication


class UIMaster:
    _instance = None

    def __init__(self):
        super().__init__()
        self.topLevel = QApplication.topLevelWidgets()[0]
        self._compiledPrograms: List[ProgramCompilation.CompiledProgram] = []
        self._programLookup: Dict[Program, ProgramCompilation.CompiledProgram] = {}
        self.rig = Rig()
        self.rig.allDevices = []
        try:
            self.rig.allDevices = LoadObject(Path("devices.pkl"))
        except EOFError:
            pass
        except IOError:
            pass
        self.currentChip = Chip()
        self.modified = False
        self.currentChipPath: Optional[Path] = None
        self.currentCursorShape: Optional[QCursor] = None

    @staticmethod
    def Shutdown():
        self = UIMaster.Instance()
        self.rig.Disconnect()
        SaveObject(self.rig.allDevices, Path("devices.pkl"))

    @staticmethod
    def CompileProgram(program: Program):
        self = UIMaster.Instance()
        if program not in self._programLookup:
            self._programLookup[program] = ProgramCompilation.CompiledProgram(program)
            self._compiledPrograms.append(self._programLookup[program])
        ProgramCompilation.Recompile(self._programLookup[program], self.currentChip, self.rig,
                                     self._compiledPrograms)

    @staticmethod
    def RemoveProgram(program: Program):
        self = UIMaster.Instance()
        if program not in self._programLookup:
            return
        self._compiledPrograms.remove(self._programLookup[program])
        del self._programLookup[program]

    @staticmethod
    def GetCompiledPrograms():
        self = UIMaster.Instance()
        return self._compiledPrograms

    @staticmethod
    def GetCompiledProgram(program: Program):
        self = UIMaster.Instance()
        if program not in self._programLookup or \
                ProgramCompilation.IsOutOfDate(self._programLookup[program]):
            self.CompileProgram(program)
        return self._programLookup[program]

    @staticmethod
    def Instance():
        if UIMaster._instance is None:
            UIMaster._instance = UIMaster()
        return UIMaster._instance

    @staticmethod
    def StyleSheet():
        f = open("UI/stylesheet.css")
        ss = f.read()
        f.close()
        return ss

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
