import time
import typing

from Program import Program, ProgramInstance, ProgramChipInterface
from Model.Valve import ValveState


class ScriptedProgram(Program):
    class Timer:
        def __init__(self, duration: float, delegate: typing.Optional[typing.Callable] = None,
                     repeated=False):
            self.startTime = time.time()
            self.duration = duration
            self.delegate = delegate
            self.repeated = repeated
            self._isRunning = False

        def Start(self):
            self.startTime = time.time()
            self._isRunning = True

        def Stop(self):
            self._isRunning = False

        def IsRunning(self):
            return self._isRunning

        def Tick(self):
            if time.time() - self.startTime >= self.duration:
                if self.delegate:
                    self.delegate()
                if self.repeated:
                    self.Start()
                else:
                    self.Stop()

    def __init__(self):
        super().__init__()
        self.name = "New Scripted Program"

        self.startScript = """"""  # Called on start
        self.tickScript = """"""  # Called once per tick
        self.stopScript = """"""  # Called when the program is stopped or finishes

    def OnStart(self, instance: 'ScriptedProgramInstance'):
        exec(self.startScript, self.MakeScriptGlobals(instance), instance.localEnv)

    def OnTick(self, instance: 'ScriptedProgramInstance'):
        exec(self.tickScript, self.MakeScriptGlobals(instance), instance.localEnv)
        for timer in instance.timers:
            if timer.IsRunning():
                timer.Tick()
        instance.lastTickTime = time.time()
        for subDelegate in instance.subDelegates.keys():
            if not subDelegate.IsRunning():
                instance.subDelegates[subDelegate]()
                del instance.subDelegates[subDelegate]

    def OnStop(self, instance: 'ScriptedProgramInstance'):
        exec(self.stopScript, self.MakeScriptGlobals(instance), instance.localEnv)

    @staticmethod
    def MakeScriptGlobals(instance: 'ScriptedProgramInstance'):
        return {"GetParameter": lambda name: instance.GetParameterValue(name),
                "SetOutput": lambda name, value: instance.SetOutputValue(name, value),
                "GetValveState": lambda name: instance.GetChipInterface().GetValveWithName(name).GetState(),
                "SetValveState": lambda name, state: instance.GetChipInterface().GetValveWithName(name).SetState(state),
                "Program": lambda name: instance.GetChipInterface().GetProgramWithName(name).CreateInstance(
                    instance.GetChipInterface()),
                "Run": lambda programInstance, onFinish=None: ScriptedProgram.StartSubProgram(instance, programInstance,
                                                                                              onFinish),
                "Stop": lambda: instance.Stop(),
                "OPEN": ValveState.OPEN,
                "CLOSED": ValveState.CLOSED,
                "Timer": ScriptedProgram.Timer,
                "deltaTime": time.time() - instance.lastTickTime,
                "timeSinceStart": time.time() - instance.startTime}

    @staticmethod
    def StartSubProgram(instance: 'ScriptedProgramInstance', subInstance: ProgramInstance,
                        onFinish: typing.Optional[typing.Callable]):
        subInstance.Start(instance)
        if onFinish:
            instance.subDelegates[subInstance] = onFinish

    def CreateInstance(self, chipInterface: 'ProgramChipInterface') -> 'ProgramInstance':
        return ScriptedProgramInstance(self, chipInterface)


class ScriptedProgramInstance(ProgramInstance):
    def __init__(self, program: ScriptedProgram, chipInterface: ProgramChipInterface):
        super().__init__(program, chipInterface)
        self.startTime = time.time()
        self.lastTickTime = time.time()
        self.localEnv = {}
        self.subDelegates: typing.Dict[ProgramInstance, typing.Callable] = {}
        self.timers: typing.List[ScriptedProgram.Timer] = []
        self.finishing = False
