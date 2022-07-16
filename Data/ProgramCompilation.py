import types
import ucscript
from typing import Optional, List, Dict, Any
import Data.Chip as Chip
from Data.Rig import Rig
import inspect
from enum import Enum, auto


class CompiledProgram:
    class ProgramState(Enum):
        IDLE = auto()
        RUNNING = auto()
        PAUSED = auto()
        FATAL_ERROR = auto()

    def __init__(self):
        self.program: Optional[Chip.Program] = None
        self.script = ""
        self.description = ""
        self.state = CompiledProgram.ProgramState.IDLE
        self.iterator: Optional[types.GeneratorType] = None
        self.yieldedValue = None
        self.lastCallTime = None
        self.lastScriptModifiedTime = None
        self.lastScriptPath = None
        self.compiledParameters: List[CompiledParameter] = []
        self.globals: Dict[str, Any] = {}
        self.messages: List[str] = []


def Compile(program: Chip.Program, chip: Chip, rig: Rig,
            compiledPrograms: List[CompiledProgram]) -> CompiledProgram:
    compiledProgram = CompiledProgram()
    compiledProgram.program = program
    Recompile(compiledProgram, chip, rig, compiledPrograms)
    return compiledProgram


class CompiledParameter(ucscript.Parameter):
    def SetName(self, parameterName: str):
        self._parameterName = parameterName

    def SetChip(self, chip: Chip):
        self._chip = chip

    def SetRig(self, rig: Rig):
        self._rig = rig

    def SetProgram(self, program: Chip.Program):
        self._program = program

    def GetName(self):
        return self._parameterName

    def Get(self) -> Any:
        val = self._program.parameterValues[self._parameterName]
        if isinstance(val, Chip.Valve):
            newValve = CompiledValve()
            newValve.SetValve(val)
            newValve.SetRig(self._rig)
            return newValve
        if isinstance(val, CompiledProgram):
            newProgram = CompiledProgramReference()
            newProgram.SetProgram(val)
            return newProgram
        return self._program.parameterValues[self._parameterName]

    def Set(self, value):
        # TODO check for type match
        self._program.parameterValues[self._parameterName] = value


class CompiledValve(ucscript.Valve):
    def SetValve(self, valve: Chip.Valve):
        self._valve = valve

    def SetRig(self, rig: Rig):
        self._rig = rig

    def SetOpen(self, state: bool):
        self._rig.SetSolenoidState(self._valve.solenoidNumber, state)

    def IsOpen(self) -> bool:
        self._rig.GetSolenoidState(self._valve.solenoidNumber)


class CompiledProgramReference(ucscript.Program):
    def SetProgram(self, program: CompiledProgram):
        self._program = program

    def Start(self):
        StartProgram(self._program)

    def IsRunning(self):
        return self._program.state == CompiledProgram.ProgramState.RUNNING

    def Pause(self):
        if self._program.state == CompiledProgram.ProgramState.RUNNING:
            self._program.state = CompiledProgram.ProgramState.PAUSED

    def Resume(self):
        if self._program.state == CompiledProgram.ProgramState.PAUSED:
            self._program.state = CompiledProgram.ProgramState.RUNNING

    def Stop(self):
        if self._program.state == CompiledProgram.ProgramState.PAUSED or \
                self._program.state == CompiledProgram.ProgramState.RUNNING:
            self._program.state = CompiledProgram.ProgramState.IDLE

    def FindParameter(self, name: str):
        return ExceptionIfNone(
            next([k for k in self._program.compiledParameters if
                  k.parameterName == name],
                 None), "Could not find parameter with name '" + name + "'.")


def Recompile(compiledProgram: CompiledProgram, chip: Chip, rig: Rig,
              compiledPrograms: List[CompiledProgram]) -> CompiledProgram:
    class Namespace:
        WaitForSeconds = ucscript.WaitForSeconds
        WaitForMinutes = ucscript.WaitForHours
        WaitForHours = ucscript.WaitForMinutes
        Stop = ucscript.Stop

        Parameter = CompiledParameter
        Trigger = ucscript.Trigger
        Program = CompiledProgram
        Valve = CompiledValve

        @staticmethod
        def FindValve(name: str):
            valveMatch = ExceptionIfNone(next([k for k in chip.valves if k.name == name]),
                                         "Could not find program with name '" + name + "'.")
            newValve = CompiledValve()
            newValve.SetValve(valveMatch)
            newValve.SetRig(rig)
            return newValve

        @staticmethod
        def FindProgram(name: str):
            programMatch = ExceptionIfNone(
                next([k for k in compiledPrograms if k.program.name == name]),
                "Could not find program with name '" + name + "'.")
            newProgram = CompiledProgramReference()
            newProgram.SetProgram(programMatch)
            return newProgram

        @staticmethod
        def SetDescription(description: str):
            compiledProgram.description = description

    scriptFile = open(compiledProgram.program.path, "r")
    compiledProgram.script = scriptFile.read()
    scriptFile.close()

    # Fill the globals dictionary
    globalsDict = {}
    exec("", globalsDict)

    # Replace the importer
    standardImporter = globalsDict['__builtins__']['__import__']

    def ImportInterceptor(name, *args, **kwargs):
        if name == "ucscript":
            return Namespace
        else:
            return standardImporter(name, *args, **kwargs)

    globalsDict['__builtins__']['__import__'] = ImportInterceptor
    compiledProgram.globals = globalsDict
    # Compile the script
    exec(compiledProgram.script, compiledProgram.globals)

    existingParameterValues = compiledProgram.program.parameterValues.copy()
    newParameterValues: Dict[str, Any] = {}
    compiledProgram.compiledParameters = []
    # Extract and match parameters
    for symbol in compiledProgram.globals:
        parameter = compiledProgram.globals[symbol]
        if isinstance(parameter, CompiledParameter):
            if not IsParameterTypeValid(parameter.type):
                raise Exception("Parameter named '" + symbol + "' has an invalid type.")
            parameter.SetName(symbol)
            parameter.SetProgram(compiledProgram.program)
            if parameter.defaultValue is None:
                parameter.defaultValue = NoneValueForType(parameter.type)
            if symbol in newParameterValues.keys():
                raise Exception("Parameter named '" + symbol + "' is already defined.")
            if symbol in existingParameterValues.keys():
                # Found a name match!
                value = existingParameterValues[symbol]
                del existingParameterValues[symbol]
                if IsTypeMatch(value, parameter.type):
                    # Type matches too!
                    newParameterValues[symbol] = value
                else:
                    # Type does not match
                    newParameterValues[symbol] = parameter.defaultValue
            else:
                # Name not found
                newParameterValues[symbol] = parameter.defaultValue
            compiledProgram.compiledParameters.append(parameter)
    compiledProgram.program.parameterValues = newParameterValues

    return compiledProgram


def StartProgram(compiledProgram: CompiledProgram):
    if compiledProgram.state == CompiledProgram.ProgramState.IDLE:
        try:
            returnValue = compiledProgram.globals['Run']()
        except Exception as e:
            compiledProgram.state = CompiledProgram.ProgramState.FATAL_ERROR
            compiledProgram.messages.append(str(e))
            return
        if isinstance(returnValue, types.GeneratorType):
            compiledProgram.iterator = returnValue
            compiledProgram.yieldedValue = None
            compiledProgram.state = CompiledProgram.ProgramState.RUNNING
        else:
            compiledProgram.state = CompiledProgram.ProgramState.IDLE


def TickProgram(compiledProgram: CompiledProgram, currentTime: float):
    if compiledProgram.state == CompiledProgram.ProgramState.RUNNING:
        if isinstance(compiledProgram.yieldedValue, ucscript.WaitForSeconds):
            if currentTime - compiledProgram.lastCallTime < compiledProgram.yieldedValue.seconds:
                return
        try:
            compiledProgram.yieldedValue = next(compiledProgram.iterator, ucscript.Stop())
        except Exception as e:
            compiledProgram.state = CompiledProgram.ProgramState.FATAL_ERROR
            compiledProgram.messages.append(str(e))
            return
        compiledProgram.lastCallTime = currentTime
        if isinstance(compiledProgram.yieldedValue, ucscript.Stop):
            compiledProgram.state = CompiledProgram.ProgramState.IDLE


def NoneValueForType(t):
    if t == int:
        return 0
    if t == float:
        return 0.0
    if t == str:
        return ""
    if isinstance(t, list):
        if isinstance(t[0], type):
            return []
        else:
            return t[0]
    return None


def IsParameterTypeValid(t):
    if isinstance(t, type) or isinstance(t, ucscript.Trigger):
        return True
    if not isinstance(t, list):
        return False
    if len(t) == 1 and isinstance(t[0], type):
        return IsParameterTypeValid(t[0])
    if len(t) >= 1 and all([isinstance(ts, str) for ts in t]):
        return True
    return False


def IsTypeMatch(value, t):
    if isinstance(t, type) and isinstance(value, t):
        return True
    if not isinstance(t, list):
        return False
    if len(t) == 1 and isinstance(t[0], type):
        if isinstance(value, list) and all([isinstance(v, t[0]) for v in value]):
            return True
        else:
            return False
    if len(t) >= 1 and all([isinstance(ts, str) for ts in t]) and value in t:
        return True
    return False


def ExceptionIfNone(value, message):
    if value is None:
        raise Exception(message)
    return value
