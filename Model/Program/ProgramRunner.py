import time
import types
from typing import Optional, Dict

from Model.Valve import ValveState

from Model.Program.Data import DataValueType
from Model.Program.ProgramInstance import ProgramInstance
from Model.Chip import Chip


class ProgramRunner:
    class WaitForSeconds:
        def __init__(self, duration):
            self.duration = duration

    class RunningProgramInfo:
        def __init__(self):
            self.parentProgram: Optional[ProgramInstance] = None
            self.waitStartTime = -1
            self.waitDuration = 0
            self.waitingForProgram: Optional[ProgramInstance] = None
            self.isPaused = False
            self.iterator: Optional[types.GeneratorType] = None

    def __init__(self, chip: Chip):
        # Map from instance -> parent instance
        self.runningPrograms: Dict[ProgramInstance, ProgramRunner.RunningProgramInfo] = {}
        self.chip = chip

    def Tick(self):
        for programInstance in self.runningPrograms.copy():
            info = self.runningPrograms[programInstance]
            if info.isPaused or (time.time() - info.waitStartTime) < info.waitDuration:
                continue
            if info.waitingForProgram in self.runningPrograms:
                continue
            else:
                info.waitingForProgram = None
            yieldValue = next(self.runningPrograms[programInstance].iterator, None)
            if isinstance(yieldValue, ProgramInstance):
                info.waitingForProgram = yieldValue
            elif isinstance(yieldValue, ProgramRunner.WaitForSeconds):
                info.waitStartTime = time.time()
                info.waitDuration = yieldValue.duration
            elif yieldValue is None:
                self.Stop(programInstance)
            else:
                raise Exception("Yielded object must be of type WaitForSeconds, ProgramInstance, or NoneType.")

    def IsPaused(self, instance: ProgramInstance):
        return instance in self.runningPrograms and self.runningPrograms[instance].isPaused

    def IsRunning(self, instance: ProgramInstance):
        return instance in self.runningPrograms

    def Stop(self, instance: ProgramInstance):
        # Check if it is running
        if not self.IsRunning(instance):
            raise Exception("Program is not running")
        # Stop all child programs
        for programInstance in self.runningPrograms.copy():
            if self.runningPrograms[programInstance].parentProgram == instance:
                self.Stop(programInstance)
        # Remove it from the list
        del self.runningPrograms[instance]

    def Pause(self, instance: ProgramInstance):
        if not self.IsRunning(instance):
            raise Exception("Program is not running")
        self.runningPrograms[instance].isPaused = True

    def Resume(self, instance: ProgramInstance):
        if not self.IsRunning(instance):
            raise Exception("Program is not running!")
        self.runningPrograms[instance].isPaused = False

    def Run(self, instance: ProgramInstance, parentInstance: Optional[ProgramInstance] = None):
        if not self.IsRunning(instance):
            raise Exception("Program is already running.")

        globalEnv = {
            'GetParameter': lambda name: instance.GetParameterWithName(name),
            "GetValve": lambda name: self.GetValveWithName(name),
            "Run": lambda programName, parameters=None: self.Run(self.BuildProgram(programName, parameters), instance),
            "IsRunning": lambda programInstance: self.IsRunning(programInstance),
            "Stop": lambda programInstance: self.Stop(programInstance),
            "Pause": lambda programInstance: self.Pause(programInstance),
            "IsPaused": lambda programInstance: self.IsPaused(programInstance),
            "Resume": lambda programInstance: self.Resume(programInstance),
            "WaitForSeconds": ProgramRunner.WaitForSeconds,
            "OPEN": ValveState.OPEN,
            "CLOSED": ValveState.CLOSED
        }

        localEnv = {}
        exec(self.FormatScript(instance.program.script), globalEnv, localEnv)
        Execute = localEnv['Execute']
        iterator = Execute()
        if isinstance(iterator, types.GeneratorType):
            # The new program is a coroutine, need to add it to the list of programs
            self.runningPrograms[instance] = ProgramRunner.RunningProgramInfo()
            self.runningPrograms[instance].parentProgram = parentInstance

        return instance

    def BuildProgram(self, programName: str, parameterValues: Optional[Dict[str, DataValueType]]):
        instance = ProgramInstance(self.GetProgramWithName(programName))
        if parameterValues is not None:
            for parameterName in parameterValues:
                instance.parameterValues[instance.GetParameterWithName(parameterName)] = parameterValues[parameterName]
        return instance

    def GetValveWithName(self, valveName: str):
        matches = [valve for valve in self.chip.valves if valve.name == valveName]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find valve with name '" + valveName + "'.")

    def GetProgramWithName(self, programName: str):
        matches = [program for program in self.chip.programs if program.name == programName]
        if matches:
            return matches[0]
        else:
            raise Exception("Could not find program with name '" + programName + "'.")

    @staticmethod
    def FormatScript(script):
        header = "def Execute():\n    "

        if script:
            return header + script.replace("\n", "\n    ").replace("\t", "    ")
        else:
            return header + "pass"
