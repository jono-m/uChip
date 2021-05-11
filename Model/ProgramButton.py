from typing import Set

from PySide6.QtCore import QPointF
from Model.Program.Program import Program
from Model.Program.ProgramInstance import ProgramInstance
from Model.Program.Parameter import Parameter


class ProgramButton:
    def __init__(self, program: Program):
        self.position = QPointF(0, 0)

        self.instance = ProgramInstance(program)
        self._lockedParameters: Set[Parameter] = set()

    def SetParameterLocked(self, parameter: Parameter, locked: bool):
        if locked:
            self._lockedParameters.add(parameter)
        elif parameter in self._lockedParameters:
            self._lockedParameters.remove(parameter)

        self._lockedParameters = {parameter for parameter in self._lockedParameters if
                                  parameter in self.instance.program.parameters}
