from typing import List, Dict, Any, Optional
from Parameter import Parameter
from ProgramInstanceState import ProgramInstanceState, ParameterValuesType
from Output import Output
from Data import DataValueType
from abc import ABC, abstractmethod
from Model.Valve import Valve

OutputValuesType = Dict[Output, DataValueType]


class Program:
    def __init__(self, name="New Program", parameters: Optional[List[Parameter]] = None,
                 outputs: Optional[List[Output]] = None):
        if outputs is None:
            outputs = []
        if parameters is None:
            parameters = []
        self._parameters = parameters
        self._outputs = outputs
        self._name = name

    def SetName(self, name: str):
        self._name = name

    def GetName(self):
        return self._name

    def GetOutputs(self):
        return self._outputs

    def GetOutputNames(self):
        return [output.GetName() for output in self._outputs]

    def GetOutputWithName(self, outputName: str):
        if not isinstance(outputName, str):
            raise Exception("Outputs should be referenced by a string.")
        matches = [output for output in self._outputs if outputName == output.GetName()]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find output with name '" + outputName + "'.")

    def AddOutput(self, output: Output):
        self._outputs.append(output)

    def RemoveOutput(self, output: Output):
        self._outputs.remove(output)

    def GetParameters(self):
        return self._parameters

    def GetParameterNames(self):
        return [parameter.GetName() for parameter in self._parameters]

    def GetParameterWithName(self, parameterName: str):
        if not isinstance(parameterName, str):
            raise Exception("Parameters should be referenced by a string.")
        matches = [parameter for parameter in self._parameters if parameterName == parameter.GetName()]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find parameter with name '" + parameterName + "'.")

    def AddParameter(self, parameter: Parameter):
        self._parameters.append(parameter)

    def RemoveParameter(self, parameter: Parameter):
        self._parameters.remove(parameter)

    def ComputeOutputs(self, parameters: ParameterValuesType) -> OutputValuesType:
        return {}

    def OnStart(self, state: ProgramInstanceState, interface: 'ProgramChipInterface'):
        pass

    def OnTick(self, state: ProgramInstanceState, interface: 'ProgramChipInterface'):
        pass

    def OnStop(self, state: ProgramInstanceState, interface: 'ProgramChipInterface'):
        pass

    def CreateInstance(self) -> ProgramInstanceState:
        newInstance = ProgramInstanceState()
        newInstance.SyncParameters(self._parameters)
        return newInstance


class ProgramChipInterface(ABC):
    @abstractmethod
    def GetValves(self) -> List[Valve]:
        pass

    def GetValveWithName(self, valveName: str):
        matches = [valve for valve in self.GetValves() if valve.GetName() == valveName]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find valve with name '" + valveName + "'.")

    @abstractmethod
    def GetPrograms(self) -> List[Program]:
        pass

    def GetProgramWithName(self, programName: str):
        matches = [program for program in self.GetPrograms() if program.GetName() == programName]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find program with name '" + programName + "'.")
