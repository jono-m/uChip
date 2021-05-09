from typing import Dict, Optional, Callable, Type, List

from ProgramInstanceState import ProgramInstanceState
from Program import Program, ProgramChipInterface
from Output import Output
from Parameter import Parameter
from Data import DataValueType
from Model.Valve import Valve, ValveState


class ScriptedProgramInstanceState(ProgramInstanceState):
    def __init__(self):
        super().__init__()
        self.localEnv = {}


class ScriptedProgram(Program):
    def __init__(self):
        super().__init__("New Scripted Program")
        self.name = "New Scripted Program"

        self.computeOutputsScript = """"""
        self.startScript = """"""
        self.pauseScript = """"""
        self.resumeScript = """"""
        self.tickScript = """"""
        self.finishScript = """"""
        self.stopScript = """"""

    def ComputeOutputs(self, state: ScriptedProgramInstanceState, interface: 'ProgramChipInterface'):
        globalEnv = {
            'GetParameter': lambda name: state.GetParameterValue(self.GetParameterWithName(self.GetParameters(), name)),
            "Compute": lambda programName, parameters=None: self.ComputeSubProgram(programName, interface,
                                                                                   parameters)}
        outputs: Dict[str, DataValueType] = exec(self.computeOutputsScript, globalEnv, {})

        if not isinstance(outputs, dict):
            raise Exception("Outputs should be a dictionary of output names to values.")

        extracted = {}
        for outputName in outputs:
            output = self.GetOutputWithName(self.GetOutputs(), outputName)
            state.SetOutputValue(output, outputs[outputName])

        return extracted

    def OnStart(self, state: ScriptedProgramInstanceState, chipInterface: 'ProgramChipInterface'):
        self.RunStepScript(self.startScript, state, chipInterface)

    def OnPause(self, state: ScriptedProgramInstanceState, chipInterface: 'ProgramChipInterface'):
        self.RunStepScript(self.pauseScript, state, chipInterface)

    def OnResume(self, state: ScriptedProgramInstanceState, chipInterface: 'ProgramChipInterface'):
        self.RunStepScript(self.resumeScript, state, chipInterface)

    def OnTick(self, state: ScriptedProgramInstanceState, chipInterface: 'ProgramChipInterface'):
        self.RunStepScript(self.tickScript, state, chipInterface)

    def OnFinish(self, state: ScriptedProgramInstanceState, chipInterface: 'ProgramChipInterface'):
        self.RunStepScript(self.finishScript, state, chipInterface)

    def OnStop(self, state: ScriptedProgramInstanceState, chipInterface: 'ProgramChipInterface'):
        self.RunStepScript(self.stopScript, state, chipInterface)

    def RunStepScript(self, script: str, state: ScriptedProgramInstanceState, interface: ProgramChipInterface):
        globalEnv = {
            'GetParameter': lambda name: state.GetParameterValue(self.GetParameterWithName(self.GetParameters(), name)),
            "GetValveState": lambda name: self.GetValveWithName(interface.GetValves(), name),
            "SetValveState": lambda name, valveState: self.GetValveWithName(interface.GetValves(), name).SetState(
                valveState),
            "Compute": lambda programName, parameters=None: self.ComputeSubProgram(programName, interface,
                                                                                   parameters),
            "StartProgram": lambda programName, parameters=None, doneDelegate=None: self.StartSubProgram(
                programName,
                parameters,
                doneDelegate,
                interface,
                state),
            "StopProgram": lambda programState: interface.FinishProgram(programState),
            "Finish": lambda: interface.FinishProgram(state),
            "OPEN": ValveState.OPEN,
            "CLOSED": ValveState.CLOSED}
        exec(script, globalEnv, state.localEnv)

    @staticmethod
    def GetStateType() -> Type[ProgramInstanceState]:
        return ScriptedProgramInstanceState

    @staticmethod
    def ComputeSubProgram(programName: str, interface: ProgramChipInterface,
                          parameters: Optional[Dict[str, DataValueType]]):
        program = ScriptedProgram.GetProgramWithName(interface.GetPrograms(), programName)
        instance = program.CreateInstance()
        if parameters is not None:
            for parameterName in parameters:
                instance.SetParameterValue(ScriptedProgram.GetParameterWithName(program.GetParameters(), parameterName),
                                           parameters[parameterName])

        program.ComputeOutputs(instance, interface)
        return {output.GetName(): instance.GetOutputValue(output) for output in program.GetOutputs()}

    @staticmethod
    def StartSubProgram(programName: str, parameters: Optional[Dict[str, DataValueType]], doneDelegate: Callable,
                        interface: ProgramChipInterface, parentState: ProgramInstanceState):
        program = ScriptedProgram.GetProgramWithName(interface.GetPrograms(), programName)
        instance = program.CreateInstance()
        if parameters is not None:
            for parameterName in parameters:
                instance.SetParameterValue(ScriptedProgram.GetParameterWithName(program.GetOutputs(), parameterName),
                                           parameters[parameterName])

        interface.StartProgram(program, instance, parentState, doneDelegate)

        return instance

    @staticmethod
    def GetOutputWithName(outputs: List[Output], outputName: str):
        if not isinstance(outputName, str):
            raise Exception("Outputs should be referenced by a string.")
        matches = [output for output in outputs if outputName == output.GetName()]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find output with name '" + outputName + "'.")

    @staticmethod
    def GetParameterWithName(parameters: List[Parameter], parameterName: str):
        if not isinstance(parameterName, str):
            raise Exception("Parameters should be referenced by a string.")
        matches = [parameter for parameter in parameters if parameterName == parameter.GetName()]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find parameter with name '" + parameterName + "'.")

    @staticmethod
    def GetValveWithName(valves: List[Valve], valveName: str):
        matches = [valve for valve in valves if valve.GetName() == valveName]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find valve with name '" + valveName + "'.")

    @staticmethod
    def GetProgramWithName(programs: List[Program], programName: str):
        matches = [program for program in programs if program.GetName() == programName]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find program with name '" + programName + "'.")
