from typing import Optional, List

from Model.Valve import Valve
from Model.Program.Data import DataType
from Model.Program.Program import Program
from Model.Program.ProgramPreset import ProgramPreset
from Model.Image import Image
from Model.Annotation import Annotation
from pathlib import Path
import dill

import os


class Chip:
    def __init__(self):
        self.valves: List[Valve] = []
        self.programs: List[Program] = []
        self.programPresets: List[ProgramPreset] = []
        self.images: List[Image] = []
        self.annotations: List[Annotation] = []
        self.editingMode = True
        self.path: Optional[Path] = None
        self.modified = False

    def RecordModification(self):
        self.modified = True

    def HasBeenSaved(self):
        return bool(self.path)

    def SaveToFile(self, path: Path):
        self.path = path
        self.modified = False
        for image in self.images:
            image.path = Path(os.path.relpath(image.path, self.path.parent))
        file = open(self.path, "wb+")
        dill.dump(self, file)
        file.close()
        for image in self.images:
            image.path = path.parent / image.path

    @staticmethod
    def LoadFromFile(path: Path) -> 'Chip':
        file = open(path, "rb")
        chip = dill.load(file)
        file.close()
        chip.path = path
        for image in chip.images:
            image.path = path.parent / image.path
        return chip

    def NextSolenoidNumber(self):
        number = 0
        while True:
            if number not in [valve.solenoidNumber for valve in self.valves]:
                return number
            number += 1

    def FindValveWithName(self, valveName: str):
        matches = [valve for valve in self.valves if valve.name == valveName]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find valve with name '" + valveName + "'.")

    def FindProgramWithName(self, programName: str):
        matches = [program for program in self.programs if program.name == programName]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find program with name '" + programName + "'.")

    def FindPresetWithName(self, presetName: str):
        print("Looking for item")
        matches = [preset for preset in self.programPresets if preset.name == presetName]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find preset with name '" + presetName + "'.")

    def Validate(self):
        for preset in self.programPresets.copy():
            if preset.instance.program not in self.programs:
                self.programPresets.remove(preset)
            else:
                preset.instance.SyncParameters()

                for parameter in preset.instance.parameterValues:
                    if parameter.dataType is DataType.VALVE:
                        if preset.instance.parameterValues[parameter] not in self.valves:
                            preset.instance.parameterValues[parameter] = None
                    elif parameter.dataType is DataType.PROGRAM_PRESET:
                        if preset.instance.parameterValues[parameter] not in self.programPresets:
                            preset.instance.parameterValues[parameter] = None
