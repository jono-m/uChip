import types
from typing import List, Dict, Any, Optional
from enum import Enum, auto


class ProgramSpecification:
    def __init__(self):
        self.parameters: List[Parameter] = []
        self.name = "New Program"
        self.description = ""
        self.script = """"""


def FormatScriptForProgram(script: str):
    header = "def Execute():\n    "

    if script:
        return header + script.replace("\n", "\n    ").replace("\t", "    ")
    else:
        return header + "pass"


class ParameterType(Enum):
    INTEGER = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    STRING = auto()
    VALVE = auto()
    PROGRAM = auto()
    LIST = auto()
    CUSTOM = auto()

    def GetInitialValue(self):
        return {ParameterType.INTEGER: 0,
                ParameterType.FLOAT: 0.0,
                ParameterType.BOOLEAN: False,
                ParameterType.STRING: "",
                ParameterType.VALVE: None,
                ParameterType.PROGRAM: None,
                ParameterType.LIST: [],
                ParameterType.CUSTOM: None}[self]

    def ToString(self):
        return {ParameterType.INTEGER: "Integer",
                ParameterType.FLOAT: "Float",
                ParameterType.BOOLEAN: "Boolean",
                ParameterType.STRING: "String",
                ParameterType.VALVE: "Valve",
                ParameterType.PROGRAM: "Program",
                ParameterType.LIST: "List",
                ParameterType.CUSTOM: "Other"}[self]


class Parameter:
    def __init__(self):
        self.name = "New Parameter"
        self.dataType = ParameterType.INTEGER

        self.defaultValues = {dataType: dataType.GetDefaultValue() for dataType in ParameterType}

        self.hasMinimum = False
        self.hasMaximum = False
        self.minimum = 0
        self.maximum = 100
        self.listType = ParameterType.INTEGER


class ProgramState(Enum):
    IDLE = auto()
    WAITING = auto()
    RUNNING = auto()
    ERROR = auto()


class ProgramInstance:
    def __init__(self):
        self.specification: Optional[ProgramSpecification] = None
        self.parameterValues: Dict[Parameter, Any] = {}
        self.state = ProgramState.IDLE
        self.paused = False
        self.iterator: Optional[types.GeneratorType] = None
        self.yieldedValue = None
        self.lastCallTime = None
        self.messages: List[str] = []


class Stop:
    pass


class WaitForSeconds:
    def __init__(self, seconds):
        self.seconds = seconds


class WaitForMinutes(WaitForSeconds):
    def __init__(self, minutes):
        super().__init__(minutes * 60)


class WaitForHours(WaitForMinutes):
    def __init__(self, hours):
        super().__init__(hours * 60)


class WaitForProgram:
    def __init__(self, instance: ProgramInstance):
        self.instanceToWaitFor = instance


def InstantiateProgram(program: ProgramSpecification):
    instance = ProgramInstance()
    instance.parameterValues = {parameter: parameter.defaultValues[parameter.dataType]
                                for parameter in program.parameters}
    instance.parameterVisibility = {parameter: True for parameter in program.parameters}
    return instance


def StartInstance(instance: ProgramInstance, environment):
    if instance.state != ProgramState.IDLE:
        return

    try:
        script = FormatScriptForProgram(instance.specification.script)
        local = {}
        exec(script, environment, local)
        executedProgram = local['Execute']()
    except Exception as e:
        CrashInstance(instance, str(e))
        return
    else:
        if isinstance(executedProgram, types.GeneratorType):
            instance.iterator = executedProgram
            instance.state = ProgramState.RUNNING


def UpdateInstance(instance: ProgramInstance, currentTime: float):
    if instance.paused:
        return
    if instance.state == ProgramState.RUNNING:
        try:
            yieldValue = next(instance.iterator, Stop())
        except Exception as e:
            CrashInstance(instance, str(e))
            return
        else:
            instance.yieldedValue = yieldValue
            instance.lastCallTime = currentTime

    instance.state = ProgramState.RUNNING
    if isinstance(instance.yieldedValue, WaitForSeconds):
        if currentTime - instance.lastCallTime < instance.yieldedValue.seconds:
            instance.state = ProgramState.WAITING
    elif isinstance(instance.yieldedValue, WaitForProgram):
        if instance.yieldedValue.instanceToWaitFor.state == ProgramState.RUNNING or \
                instance.yieldedValue.instanceToWaitFor.state == ProgramState.WAITING:
            instance.state = ProgramState.WAITING
        elif instance.yieldedValue.instanceToWaitFor.state == ProgramState.ERROR:
            CrashInstance(instance, "Error in waiting program " +
                          instance.yieldedValue.instanceToWaitFor.specification.name +
                          " instance:\n\t" +
                          instance.yieldedValue.instanceToWaitFor.messages[-1])
    elif isinstance(instance.yieldedValue, Stop):
        StopInstance(instance)


def UpdateInstances(instances: List[ProgramInstance], currentTime: float):
    for instance in instances:
        UpdateInstance(instance, currentTime)


def PauseInstance(instance: ProgramInstance, paused: bool):
    instance.paused = paused


def StopInstance(instance: ProgramInstance):
    instance.state = ProgramState.IDLE


def CrashInstance(instance: ProgramInstance, errorMessage: str):
    instance.messages.append(errorMessage)
    instance.state = ProgramState.ERROR
