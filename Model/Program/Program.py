import typing
from abc import ABC, abstractmethod
from Model.Valve import Valve


class Program:
    def __init__(self):
        self.parameters: typing.List[Parameter] = []
        self.outputs: typing.List[Output] = []
        self.name = "New Program"

    def OnComputeOutputs(self, instance: 'ProgramInstance'):
        pass

    def OnStart(self, instance: 'ProgramInstance'):
        pass

    def OnTick(self, instance: 'ProgramInstance'):
        instance.Stop()

    def OnStop(self, instance: 'ProgramInstance'):
        pass

    def CreateInstance(self, chipInterface: 'ProgramChipInterface') -> 'ProgramInstance':
        return ProgramInstance(self, chipInterface)


class Parameter:
    def __init__(self):
        self.name = "Parameter"
        self.dataType: typing.Type = int
        self.defaultValue = 0

        self.minimumInteger: typing.Optional[int] = None
        self.maximumInteger: typing.Optional[int] = None
        self.minimumNumber: typing.Optional[int] = None
        self.maximumNumber: typing.Optional[int] = None


class Output:
    def __init__(self):
        self.name = "Output"
        self.dataType: typing.Type = int


class ProgramChipInterface(ABC):
    @abstractmethod
    def GetValves(self) -> typing.List[Valve]:
        pass

    def GetValveWithName(self, valveName: str):
        matches = [valve for valve in self.GetValves() if valve.name == valveName]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find valve with name '" + valveName + "'.")

    @abstractmethod
    def GetPrograms(self) -> typing.List[Program]:
        pass

    def GetProgramWithName(self, programName: str):
        matches = [program for program in self.GetPrograms() if program.name == programName]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find program with name '" + programName + "'.")


class ProgramInstance:
    def __init__(self, program: Program, chipInterface: ProgramChipInterface):
        self._program = program
        self._parameterValues = self.CreateDefaultParameters()
        self._outputValues = self.CreateDefaultOutputs()
        self._programChipInterface = chipInterface
        self._children: typing.List[ProgramInstance] = []
        self._parent: typing.Optional[ProgramInstance] = None
        self._isRunning = False

    def IsRunning(self):
        return self._isRunning

    def GetChipInterface(self):
        return self._programChipInterface

    def GetParameterNames(self):
        return [parameter.name for parameter in self._program.parameters]

    def GetParameterWithName(self, parameterName: str):
        if not isinstance(parameterName, str):
            raise Exception("Parameters should be referenced by a string.")
        matches = [parameter for parameter in self._program.parameters if parameterName == parameter.name]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find parameter with name '" + parameterName + "'.")

    def GetParameterValue(self, parameter: Parameter):
        return self._parameterValues[parameter]

    def SetParameterValue(self, parameter: Parameter, value):
        self._parameterValues[parameter] = value

    def GetOutputNames(self):
        return [output.name for output in self._program.outputs]

    def GetOutputWithName(self, outputName: str):
        if not isinstance(outputName, str):
            raise Exception("Outputs should be referenced by a string.")
        matches = [output for output in self._program.outputs if outputName == outputName]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find output with name '" + outputName + "'.")

    def GetOutputValue(self, output: Output):
        return self._outputValues[output]

    def SetOutputValue(self, output: Output, value):
        self._outputValues[output] = value

    def Start(self, parentInstance: typing.Optional['ProgramInstance']):
        if self.IsRunning():
            raise Exception("Program instance '" + str(self) + "' is already running.")
        if parentInstance:
            parentInstance._children.append(self)
            self._parent = parentInstance
        self._isRunning = True
        self._program.OnStart(self)

    def ComputeOutputs(self):
        self._program.OnComputeOutputs(self)

    def Tick(self):
        if not self.IsRunning():
            raise Exception("Program is not running, but Tick() was called.")
        self._program.OnTick(self)
        for child in self._children:
            child.Tick()

    def Stop(self, force=False):
        if not self.IsRunning():
            raise Exception("Tried to stop program instance '" + str(self) + "', but it was already not running.")
        self._isRunning = False
        if not force:
            self._program.OnStop(self)
        for child in self._children.copy():
            child.Stop(force)
        if self._parent:
            self._parent._children.remove(self)

    def SyncWithProgram(self):
        self._outputValues = self.CreateDefaultParameters()

        oldParameterValues = self._parameterValues
        self._parameterValues = self.CreateDefaultParameters()

        for oldParameter in oldParameterValues:
            matches = [parameter for parameter in self._parameterValues if
                       parameter.name == oldParameter.name and parameter.dataType == oldParameter.dataType]
            if matches:
                self._parameterValues[matches[0]] = oldParameterValues[oldParameter]

    def CreateDefaultParameters(self) -> typing.Dict['Parameter']:
        return {parameter: parameter.defaultValue for parameter in self._program.parameters}

    def CreateDefaultOutputs(self):
        return {output: output.dataType() for output in self._program.outputs}
