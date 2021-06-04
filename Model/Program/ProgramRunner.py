import time
import types
from typing import Optional, Dict, List

from Model.Program.ProgramInstance import ProgramInstance
from Model.Chip import Chip
from Model.Rig import Rig


class ProgramRunner:
    def __init__(self):
        # Info about each running program
        self.runningPrograms: Dict[ProgramInstance, RunningProgramInfo] = {}

        # Programs that should be started on the next tick
        self.queuedPrograms: List[ProgramInstance] = []

        self._lastTickTime = time.time()
        self._errorList: List[ProgramRunnerError] = []

        self.chip = None
        self.rig = None

    def GetTickDelta(self):
        return time.time() - self._lastTickTime

    def StopAll(self):
        for program in self.runningPrograms.copy():
            self.Stop(program)
        self.queuedPrograms.clear()

    def GetErrors(self):
        return self._errorList

    def ClearErrors(self):
        self._errorList.clear()

    def Tick(self):
        self._lastTickTime = time.time()
        for program in self.queuedPrograms:
            self.Start(program, None)
        self.queuedPrograms.clear()

        for programInstance in self.runningPrograms.copy():
            info = self.runningPrograms[programInstance]
            if info.isPaused or (time.time() - info.waitStartTime) < info.waitDuration:
                continue
            if info.waitingForProgram in self.runningPrograms:
                continue
            else:
                info.waitingForProgram = None
            try:
                yieldValue = next(self.runningPrograms[programInstance].iterator, None)
            except Exception as e:
                self._errorList.append(ProgramRunnerError(programInstance, info, e))
                self.Stop(programInstance)
                continue
            if isinstance(yieldValue, ProgramInstance):
                info.waitingForProgram = yieldValue
            elif isinstance(yieldValue, WaitForSeconds):
                info.waitStartTime = time.time()
                info.waitDuration = yieldValue.duration
            elif yieldValue is None:
                self.Stop(programInstance)
            else:
                self._errorList.append(
                    ProgramRunnerError(programInstance, info, Exception(
                        "Yielded object must be of type WaitForSeconds, ProgramInstance, or NoneType.")))
                self.Stop(programInstance)

    def IsPaused(self, instance: ProgramInstance):
        return instance in self.runningPrograms and self.runningPrograms[instance].isPaused

    def IsRunning(self, instance: ProgramInstance):
        return instance in self.runningPrograms

    def Stop(self, instance: ProgramInstance):
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
        if self.IsRunning(instance):
            raise Exception("Program is already running.")

        if parentInstance:
            return self.Start(instance, parentInstance)
        else:
            self.queuedPrograms.append(instance)

    def Start(self, instance: ProgramInstance, parentInstance: Optional[ProgramInstance] = None):
        globalEnv = {
            'Parameter': lambda name: instance.parameterValues[instance.GetParameterWithName(name)],
            "Valve": lambda name: self.chip.FindValveWithName(name),
            "SetValve": lambda valve, state: self.rig.SetSolenoidState(valve.solenoidNumber, state, True),
            "GetValve": lambda valve: self.rig.GetSolenoidState(valve.solenoidNumber),
            "Run": lambda programName, parameters=None: self.Run(
                ProgramInstance.InstanceWithParameters(self.chip.FindProgramWithName(programName), parameters),
                instance),
            "IsRunning": lambda programInstance: self.IsRunning(programInstance),
            "Stop": lambda programInstance: self.Stop(programInstance),
            "Pause": lambda programInstance: self.Pause(programInstance),
            "IsPaused": lambda programInstance: self.IsPaused(programInstance),
            "Resume": lambda programInstance: self.Resume(programInstance),
            "WaitForSeconds": WaitForSeconds,
            "OPEN": True,
            "CLOSED": False
        }

        runInfo = RunningProgramInfo()
        runInfo.parentProgram = parentInstance
        localEnv = {}
        try:
            # Compile the program
            exec(instance.program.GetFormattedScript(), globalEnv, localEnv)
            Execute = localEnv['Execute']
            iterator = Execute()
        except Exception as e:
            self._errorList.append(ProgramRunnerError(instance, runInfo, e))
            return

        if isinstance(iterator, types.GeneratorType):
            # The new program is a coroutine, need to add it to the list of programs
            runInfo.iterator = iterator
            self.runningPrograms[instance] = runInfo

        return instance


class ProgramRunnerError:
    def __init__(self, programInstance: ProgramInstance, info: 'RunningProgramInfo',
                 exception: Exception):
        self.programInstance = programInstance
        self.info = info
        self.exception = exception


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
