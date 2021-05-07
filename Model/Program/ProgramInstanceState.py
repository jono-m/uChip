from typing import Dict, List

from Parameter import Parameter
from Data import DataValueType

ParameterValuesType = Dict[Parameter, DataValueType]


class ProgramInstanceState:
    def __init__(self):
        self._parameterValues: ParameterValuesType = {}
        self._isRunning = False

    def IsRunning(self):
        return self._isRunning

    def GetParameterValue(self, parameter: Parameter):
        return self._parameterValues[parameter]

    def SetParameterValue(self, parameter: Parameter, value):
        self._parameterValues[parameter] = value

    def Start(self):
        self._isRunning = True

    def Stop(self):
        self._isRunning = False

    def SyncParameters(self, parameters: List[Parameter]):
        oldParameterValues = self._parameterValues
        self._parameterValues = {parameter: parameter.GetDefaultValue() for parameter in parameters}

        for oldParameter in oldParameterValues:
            matches = [parameter for parameter in self._parameterValues if
                       parameter.name == oldParameter.name and parameter.dataType == oldParameter.dataType]
            if matches:
                self._parameterValues[matches[0]] = oldParameterValues[oldParameter]
