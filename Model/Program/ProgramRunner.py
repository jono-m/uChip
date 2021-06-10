import time
import types
from typing import Optional, Dict, List, Union

from Model.Program.ProgramInstance import ProgramInstance
from Model.Chip import Chip, ProgramPreset
from Model.Rig import Rig


class ProgramRunner:
    def __init__(self):
        # Info about each running program
        self.runningPrograms: Dict[ProgramInstance, RunningProgramInfo] = {}

        # Programs that should be started on the next tick
        self.queuedPrograms: List[ProgramInstance] = []

        self._lastTickTime = time.time()
        self._messageList: List[ProgramRunnerMessage] = []

        self.chip: Optional[Chip] = None
        self.rig: Optional[Rig] = None

    def CheckPrograms(self):
        for program in self.runningPrograms.copy():
            if program in self.runningPrograms:
                if program.program not in self.chip.programs:
                    self.StopAtRoot(program)

    def GetTickDelta(self):
        return time.time() - self._lastTickTime

    def StopAll(self):
        for program in self.runningPrograms.copy():
            self.Stop(program)
        self.queuedPrograms.clear()

    def GetMessages(self):
        return self._messageList

    def Report(self, message: 'ProgramRunnerMessage'):
        self._messageList.append(message)
        if message.isError:
            if self.IsRunning(message.programInstance):
                self.StopAtRoot(message.programInstance)

    def ClearMessages(self):
        self._messageList.clear()

    def Tick(self):
        self._lastTickTime = time.time()
        for program in self.queuedPrograms:
            self.Start(program, None)
        self.queuedPrograms.clear()

        for programInstance in self.runningPrograms.copy():
            if programInstance not in self.runningPrograms:
                continue
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
                self.Report(ProgramRunnerMessage(programInstance, True, str(e)))
                continue
            if isinstance(yieldValue, ProgramInstance):
                info.waitingForProgram = yieldValue
            elif isinstance(yieldValue, WaitForSeconds):
                info.waitStartTime = time.time()
                info.waitDuration = yieldValue.duration
            elif yieldValue is None:
                self.Stop(programInstance)
            else:
                self.Report(ProgramRunnerMessage(programInstance, True, str(Exception(
                    "Yielded object must be of type WaitForSeconds, ProgramInstance, or NoneType."))))

    def IsPaused(self, instance: ProgramInstance):
        if isinstance(instance, ProgramPreset):
            return self.IsPaused(instance.instance)
        return instance in self.runningPrograms and self.runningPrograms[instance].isPaused

    def IsRunning(self, instance: Union[ProgramInstance, ProgramPreset]):
        if isinstance(instance, ProgramPreset):
            return self.IsRunning(instance.instance)
        return instance in self.runningPrograms

    def Stop(self, instance: ProgramInstance):
        if isinstance(instance, ProgramPreset):
            return self.Stop(instance.instance)
        if not self.IsRunning(instance):
            raise Exception("Program is not running")
        # Stop all child programs
        for programInstance in self.runningPrograms.copy():
            if self.runningPrograms[programInstance].parentProgram == instance:
                self.Stop(programInstance)
        # Remove it from the list
        del self.runningPrograms[instance]

    def StopAtRoot(self, instance: ProgramInstance):
        if isinstance(instance, ProgramPreset):
            return self.StopAtRoot(instance.instance)
        toStop = instance
        while self.runningPrograms[toStop].parentProgram:
            toStop = self.runningPrograms[toStop].parentProgram
        self.Stop(toStop)

    def Pause(self, instance: ProgramInstance):
        if isinstance(instance, ProgramPreset):
            return self.Pause(instance.instance)
        if not self.IsRunning(instance):
            raise Exception("Program is not running")
        self.runningPrograms[instance].isPaused = True

    def Resume(self, instance: ProgramInstance):
        if isinstance(instance, ProgramPreset):
            return self.Resume(instance.instance)
        if not self.IsRunning(instance):
            raise Exception("Program is not running!")
        self.runningPrograms[instance].isPaused = False

    def Run(self, instance: ProgramInstance, parentInstance: Optional[ProgramInstance] = None):
        if isinstance(instance, ProgramPreset):
            return self.Run(instance.instance, parentInstance)
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
            "Program": lambda programName, parameters=None: ProgramInstance.InstanceWithParameters(
                self.chip.FindProgramWithName(programName), parameters),
            "Preset": lambda presetName: self.chip.FindPresetWithName(presetName).instance,
            "SetValve": lambda valve, state: self.rig.SetSolenoidState(valve.solenoidNumber, state, True),
            "GetValve": lambda valve: self.rig.GetSolenoidState(valve.solenoidNumber),
            "Start": lambda programInstance: self.Run(programInstance, instance),
            "IsRunning": lambda programInstance: self.IsRunning(programInstance),
            "Stop": lambda programInstance: self.Stop(programInstance),
            "Pause": lambda programInstance: self.Pause(programInstance),
            "IsPaused": lambda programInstance: self.IsPaused(programInstance),
            "Resume": lambda programInstance: self.Resume(programInstance),
            "print": lambda text: self.Print(instance, text),
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
            self.Report(ProgramRunnerMessage(instance, True, str(e)))
            return

        if isinstance(iterator, types.GeneratorType):
            # The new program is a coroutine, need to add it to the list of programs
            runInfo.iterator = iterator
            self.runningPrograms[instance] = runInfo

        return instance

    def Print(self, instance: ProgramInstance, text: str):
        message = ProgramRunnerMessage(instance, False, text)
        self.Report(message)


class ProgramRunnerMessage:
    def __init__(self, programInstance: ProgramInstance, isError: bool, text: str):
        self.programInstance = programInstance
        self.isError = isError
        self.text = str(text)


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
