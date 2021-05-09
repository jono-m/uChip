from typing import List, Type, Optional, Callable

from Parameter import Parameter
from ProgramInstanceState import ProgramInstanceState
from Output import Output
from abc import ABC, abstractmethod
from Model.Valve import Valve


class ProgramChipInterface(ABC):
    @abstractmethod
    def GetValves(self) -> List[Valve]:
        pass

    @abstractmethod
    def GetPrograms(self) -> List['Program']:
        pass


class ProgramRunnerInterface(ABC):
    @abstractmethod
    def StartProgram(self, program: 'Program', state: ProgramInstanceState, parentState: ProgramInstanceState,
                     finishedDelegate: Optional[Callable] = None):
        pass

    @abstractmethod
    def PauseProgram(self, state: ProgramInstanceState):
        pass

    @abstractmethod
    def ResumeProgram(self, state: ProgramInstanceState):
        pass2

    @abstractmethod
    def FinishProgram(self, state: ProgramInstanceState):
        pass

    @abstractmethod
    def StopProgram(self, state: ProgramInstanceState):
        pass

    @abstractmethod
    def GetChildPrograms(self, state: ProgramInstanceState) -> List[ProgramInstanceState]:
        pass


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

    def GetName(self):
        return self._name

    def SetName(self, name: str):
        self._name = name

    def GetOutputs(self):
        return self._outputs

    def AddOutput(self, output: Output):
        if output in self._outputs:
            raise Exception("Output already added.")
        self._outputs.append(output)

    def RemoveOutput(self, output: Output):
        if output not in self._outputs:
            raise Exception("Output was not in collection.")
        self._outputs.remove(output)

    def GetParameters(self):
        return self._parameters

    def AddParameter(self, parameter: Parameter):
        if parameter in self._parameters:
            raise Exception("Parameter already added.")
        self._parameters.append(parameter)

    def RemoveParameter(self, parameter: Parameter):
        if parameter not in self._parameters:
            raise Exception("Parameter was not in collection")
        self._parameters.remove(parameter)

    def ComputeOutputs(self, state: ProgramInstanceState, programRunnerInterface: ProgramRunnerInterface):
        pass

    def OnStart(self, state: ProgramInstanceState, chipInterface: ProgramChipInterface,
                programRunnerInterface: ProgramRunnerInterface):
        pass

    def OnPause(self, state: ProgramInstanceState, chipInterface: ProgramChipInterface,
                programRunnerInterface: ProgramRunnerInterface):
        pass

    def OnResume(self, state: ProgramInstanceState, chipInterface: ProgramChipInterface,
                 programRunnerInterface: ProgramRunnerInterface):
        pass

    def OnTick(self, state: ProgramInstanceState, chipInterface: ProgramChipInterface,
               programRunnerInterface: ProgramRunnerInterface):
        pass

    def OnFinish(self, state: ProgramInstanceState, chipInterface: ProgramChipInterface,
                 programRunnerInterface: ProgramRunnerInterface):
        pass

    def OnStop(self, state: ProgramInstanceState, chipInterface: ProgramChipInterface,
               programRunnerInterface: ProgramRunnerInterface):
        pass

    @staticmethod
    def GetStateType() -> Type[ProgramInstanceState]:
        return ProgramInstanceState

    def CreateInstance(self) -> ProgramInstanceState:
        newInstance = self.GetStateType()()
        self.InitializeInstance(newInstance)
        return newInstance

    def InitializeInstance(self, newInstance: ProgramInstanceState):
        newInstance.SyncParameters(self._parameters)
        newInstance.SyncOutputs(self._outputs)
        return newInstance
