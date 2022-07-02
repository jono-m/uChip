from typing import Dict
from Data.Program import ProgramInstance, WaitForProgram, WaitForSeconds, WaitForMinutes, \
    WaitForHours, StartInstance, ProgramState, PauseInstance, StopInstance, \
    Parameter, InstantiateProgram
from Data.Chip import Chip, Valve
from Data.Rig import Rig, SetSolenoidState, GetSolenoidState


def FindObjectWithName(objects, name: str):
    return next([o for o in list(objects) if o.name == name], None)


def ExceptionIfNone(value, message):
    if value is None:
        raise Exception(message)
    return value


class ParameterIntermediate:
    def __init__(self, parameter: Parameter, instance: ProgramInstance):
        self._parameter = parameter
        self._instance = instance

    def Set(self, value):
        # TODO: Check types, clamping...
        self._instance.parameterValues[self._parameter] = value

    def Get(self):
        return self._instance.parameterValues[self._parameter]


class ValveIntermediate:
    def __init__(self, valve: Valve, rig: Rig):
        self._valve = valve
        self._rig = rig

    def Set(self, state: bool):
        SetSolenoidState(self._rig, self._valve.solenoidNumber, state)

    def Get(self):
        GetSolenoidState(self._rig, self._valve.solenoidNumber)


class ProgramIntermediate:
    def __init__(self, instance: ProgramInstance, chip: Chip, rig: Rig,
                 programParentDictionary: Dict[ProgramInstance, ProgramInstance]):
        self._instance = instance
        self._chip = chip
        self._rig = rig
        self._programParentDictionary = programParentDictionary

    def Start(self):
        StartInstance(self._instance,
                      BuildRuntimeEnvironment(self._instance, self._chip, self._rig,
                                              self._programParentDictionary))

    def IsRunning(self):
        return self._instance.state == ProgramState.RUNNING or \
               self._instance.state == ProgramState.WAITING

    def Pause(self):
        PauseInstance(self._instance, True)

    def Stop(self):
        StopInstance(self._instance)

    def Resume(self):
        PauseInstance(self._instance, False)

    def FindParameter(self, name: str):
        return FindParameter(self._instance, name)


def FindParameter(instance: ProgramInstance, name):
    return instance.parameterValues[
               ExceptionIfNone(FindObjectWithName(instance.parameterValues.keys(), name),
                               "Could not find a parameter with name '" + name + "'")],


def CreateProgram(name: str, parentInstance: ProgramInstance, chip: Chip, rig: Rig,
                  programParentDictionary: Dict[ProgramInstance, ProgramInstance]):
    program = ExceptionIfNone(FindObjectWithName(chip.specifications, name),
                              "Could not find program with name '" + name + "'.")
    instance = InstantiateProgram(program)
    programParentDictionary[instance] = parentInstance
    return ProgramIntermediate(instance, chip, rig, programParentDictionary)


def BuildRuntimeEnvironment(instance: ProgramInstance, chip: Chip, rig: Rig,
                            programParentDictionary: Dict[ProgramInstance, ProgramInstance]):
    return {
        "FindParameter": lambda name: FindParameter(instance, name),
        "print": lambda text: instance.messages.append(text),
        "WaitForSeconds": WaitForSeconds,
        "WaitForMinutes": WaitForMinutes,
        "WaitForHours": WaitForHours,
        "WaitForProgram": WaitForProgram,
        "FindValve": lambda name: ValveIntermediate(ExceptionIfNone(
            FindObjectWithName(chip.valves, name),
            "Could not find valve with name '" + name + "'."), rig),
        "FindProgram": lambda name: ProgramIntermediate(ExceptionIfNone(
            FindObjectWithName(chip.programPresets, name),
            "Could not find existing program with name '" +
            name + "'."), chip, rig, programParentDictionary),
        "CreateProgram": lambda name: CreateProgram(name, instance, chip, rig, programParentDictionary),
        "OPEN": True,
        "CLOSED": False
    }
