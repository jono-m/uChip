from typing import List
from Model.Program.Program import Program
from Model.Chip import Chip
import dill
from pathlib import Path


class ProgramLibrary:
    _library: List[Program] = []
    libraryPath = Path("./ProgramLibrary")

    @staticmethod
    def Library():
        return ProgramLibrary._library

    @staticmethod
    def ReloadLibrary(currentChip: Chip):
        ProgramLibrary.libraryPath.mkdir(parents=True, exist_ok=True)
        paths = ProgramLibrary.libraryPath.iterdir()

        ProgramLibrary._library.clear()
        for path in paths:
            file = open(path, "rb")
            program: Program = dill.load(file)
            program.libraryPath = path
            ProgramLibrary._library.append(program)
            file.close()

        for preset in currentChip.programPresets.copy():
            if preset.instance.program.libraryPath:
                match = [p for p in ProgramLibrary._library if p.libraryPath == preset.instance.program.libraryPath]
                if match:
                    preset.instance.program = match[0]
                    preset.instance.SyncParameters()
                else:
                    currentChip.programPresets.remove(preset)
