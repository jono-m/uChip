from typing import Dict, List
from enum import Enum, auto

from Parameter import Parameter
from Output import Output
from Data import DataValueType

ParameterValuesType = Dict[Parameter, DataValueType]
OutputValuesType = Dict[Output, DataValueType]


class ProgramPhase(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()


class ProgramInstanceState:
    def __init__(self):
        self._phase = ProgramPhase.IDLE
        self._parameterValues: ParameterValuesType = {}
        self._outputValues: OutputValuesType = {}

    def GetPhase(self):
        return self._phase

    def SetPhase(self, phase: ProgramPhase):
        self._phase = phase

    def GetParameterValues(self):
        return self._parameterValues

    def GetParameterValue(self, parameter: Parameter):
        return self._parameterValues[parameter]

    def SetParameterValue(self, parameter: Parameter, value):
        self._parameterValues[parameter] = parameter.CastClamped(value)

    def GetOutputValues(self):
        return self._outputValues

    def GetOutputValue(self, output: Output):
        return self._outputValues[output]

    def SetOutputValue(self, output: Output, value):
        self._outputValues[output] = output.GetDataType().Cast(value)

    def SyncParameters(self, parameters: List[Parameter]):
        oldParameterValues = self._parameterValues
        self._parameterValues = {parameter: parameter.GetDefaultValue() for parameter in parameters}

        for oldParameter in oldParameterValues:
            if oldParameter in self._parameterValues:
                self.SetParameterValue(oldParameter, oldParameterValues[oldParameter])

    def SyncOutputs(self, outputs: List[Output]):
        oldOutputValues = self._outputValues
        self._outputValues = {output: output.GetInitialValue() for output in outputs}

        for oldOutput in oldOutputValues:
            if oldOutput in self._outputValues:
                self.SetOutputValue(oldOutput, oldOutputValues[oldOutput])
