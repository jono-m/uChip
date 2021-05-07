import time
from typing import Dict

from ProgramInstanceState import ProgramInstanceState, ParameterValuesType
from Program import Program, ProgramChipInterface, OutputValuesType
from Data import DataValueType
from Model.Valve import ValveState


class ScriptedProgramInstanceState(ProgramInstanceState):
    def __init__(self):
        super().__init__()
        self.localEnv = {}


class ScriptedProgram(Program):
    def __init__(self):
        super().__init__("New Scripted Program")
        self.name = "New Scripted Program"

        self.computeOutputsScript = """"""
        self.startScript = """"""  # Called on start
        self.tickScript = """"""  # Called once per tick
        self.stopScript = """"""  # Called when the program is stopped or finishes

    def ComputeOutputs(self, parameters: ParameterValuesType) -> OutputValuesType:
        outputs: Dict[str, DataValueType] = exec(self.computeOutputsScript,
                                                 {'GetParameter': lambda parameterName: parameters[
                                                     self.GetParameterWithName(parameterName)]},
                                                 {})
        if not isinstance(outputs, dict):
            raise Exception("Outputs should be a dictionary of output names to values.")

        extracted = {}
        for outputName in outputs:
            output = self.GetOutputWithName(outputName)
            extracted[output] = output.GetDataType().Cast(outputs[outputName])

        return extracted

    def OnStart(self, state: ScriptedProgramInstanceState, interface: 'ProgramChipInterface'):
        self.RunWithEnvironment(self.startScript, state, interface)

    def OnTick(self, state: ScriptedProgramInstanceState, interface: 'ProgramChipInterface'):
        self.RunWithEnvironment(self.tickScript, state, interface)

    def OnStop(self, state: ScriptedProgramInstanceState, interface: 'ProgramChipInterface'):
        self.RunWithEnvironment(self.stopScript, state, interface)

    def RunWithEnvironment(self, script, state: ScriptedProgramInstanceState, interface: ProgramChipInterface):
        globalEnv = {"GetParameter": lambda name: state.GetParameterValue(self.GetParameterWithName(name)),
                     "GetValveState": lambda name: interface.GetValveWithName(name),
                     "SetValveState": lambda name, valveState: interface.GetValveWithName(name).SetState(valveState),
                     "Program": lambda name: instance.GetChipInterface().GetProgramWithName(name).CreateInstance(
                         instance.GetChipInterface()),
                     "Run": lambda programInstance, onFinish=None: ScriptedProgram.StartSubProgram(instance,
                                                                                                   programInstance,
                                                                                                   onFinish),
                     "Stop": lambda: instance.Stop(),
                     "OPEN": ValveState.OPEN,
                     "CLOSED": ValveState.CLOSED,
                     "Timer": ScriptedProgram.Timer,
                     "deltaTime": time.time() - instance.lastTickTime,
                     "timeSinceStart": time.time() - instance.startTime}

    def CreateInstance(self) -> ProgramInstanceState:
        return ScriptedProgramInstanceState()
