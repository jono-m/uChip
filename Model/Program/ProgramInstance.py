from typing import Dict, Optional

from Model.Program.Parameter import Parameter
from Model.Program.Data import DataValueType
from Model.Program.Program import Program


class ProgramInstance:
    def __init__(self, program: Program):
        self.parameterValues: Dict[Parameter, DataValueType] = {}
        self.program = program
        self.SyncParameters()

    def SyncParameters(self):
        oldParameterValues = self.parameterValues
        self.parameterValues = {parameter: parameter.defaultValueDict[parameter.dataType] for parameter in
                                self.program.parameters}

        for oldParameter in oldParameterValues:
            if oldParameter in self.parameterValues:
                self.parameterValues[oldParameter] = oldParameterValues[oldParameter]

    def GetParameterWithName(self, parameterName: str):
        if not isinstance(parameterName, str):
            raise Exception("Parameters should be referenced by a string.")
        matches = [parameter for parameter in self.program.parameters if parameterName == parameter.name]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find parameter with name '" + parameterName + "'.")

    def Clone(self):
        newInstance = ProgramInstance(self.program)
        newInstance.parameterValues = self.parameterValues.copy()
        return newInstance

    @staticmethod
    def InstanceWithParameters(program: Program, parameterValues: Optional[Dict[str, DataValueType]]):
        instance = ProgramInstance(program)
        if parameterValues is not None:
            for parameterName in parameterValues:
                instance.parameterValues[instance.GetParameterWithName(parameterName)] = parameterValues[parameterName]
        return instance
