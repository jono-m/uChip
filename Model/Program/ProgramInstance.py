from typing import Dict

from Model.Program.Parameter import Parameter
from Model.Program.Data import DataValueType
from Model.Program.Program import Program


class ProgramInstance:
    def __init__(self, program: Program):
        self.parameterValues: Dict[Parameter, DataValueType] = {}
        self.program = program

    def SyncParameters(self):
        oldParameterValues = self.parameterValues
        self.parameterValues = {parameter: parameter.GetDefaultValue() for parameter in self.program.parameters}

        for oldParameter in oldParameterValues:
            if oldParameter in self.parameterValues:
                self.parameterValues[oldParameter] = oldParameterValues[oldParameter]

    def GetParameterWithName(self, parameterName: str):
        if not isinstance(parameterName, str):
            raise Exception("Parameters should be referenced by a string.")
        matches = [parameter for parameter in self.program.parameters if parameterName == parameter.GetName()]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find parameter with name '" + parameterName + "'.")
