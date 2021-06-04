import typing

from Model.Valve import Valve
from Model.Program.Data import DataType
from Model.Program.Program import Program
from Model.Program.ProgramPreset import ProgramPreset
from Model.Image import Image
from Model.Annotation import Annotation


class Chip:
    def __init__(self):
        self.valves: typing.List[Valve] = []
        self.programs: typing.List[Program] = []
        self.programPresets: typing.List[ProgramPreset] = []
        self.images: typing.List[Image] = []
        self.annotations: typing.List[Annotation] = []
        self.editingMode = True

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
                    elif parameter.dataType is DataType.PROGRAM:
                        if preset.instance.parameterValues[parameter] not in self.programs:
                            preset.instance.parameterValues[parameter] = None
                    elif parameter.dataType is DataType.PROGRAM_PRESET:
                        if preset.instance.parameterValues[parameter] not in self.programPresets:
                            preset.instance.parameterValues[parameter] = None
