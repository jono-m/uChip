import types
import ucscript
from typing import Optional, List, Dict, Any
import Data.Chip as Chip
from Data.Rig import Rig
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
        self.parameterNames: Dict[ucscript.Parameter, str] = {}
        self.globals: Dict[str, Any] = {}
        self.messages: List[str] = []


def Compile(program: Chip.Program, chip: Chip, rig: Rig, compiledPrograms: List[CompiledProgram]) -> CompiledProgram:
    compiledProgram = CompiledProgram()
    compiledProgram.program = program
    Recompile(compiledProgram, chip, rig, compiledPrograms)
    return compiledProgram


def Recompile(compiledProgram: CompiledProgram, chip: Chip, rig: Rig,
              compiledPrograms: List[CompiledProgram]) -> CompiledProgram:
    class Namespace:
        WaitForSeconds = ucscript.WaitForSeconds
        WaitForMinutes = ucscript.WaitForHours
        WaitForHours = ucscript.WaitForMinutes
        Stop = ucscript.Stop

        class Parameter(ucscript.Parameter):
            def Get(self) -> Any:
                return compiledProgram.program.parameterValues[compiledProgram.parameterNames[self]]

            def Set(self, value):
                # TODO check for type match
                compiledProgram.program.parameterValues[compiledProgram.parameterNames[self]] = value

        class Valve(ucscript.Valve):
            def __init__(self, valve: Chip.Valve):
                super().__init__()
                self._valve = valve

            def SetOpen(self, state: bool):
                rig.SetSolenoidState(self._valve.solenoidNumber, state)

            def IsOpen(self) -> bool:
                return rig.GetSolenoidState(self._valve.solenoidNumber)

        class Program(ucscript.Program):
            def __init__(self, program: CompiledProgram):
                super().__init__()
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
                    next([k for k in self._program.parameterNames if self._program.parameterNames[k] == name],
                         None), "Could not find parameter with name '" + name + "'.")

        @staticmethod
        def FindValve(name: str):
            return Namespace.Valve(ExceptionIfNone(next([k for k in chip.valves if k.name == name]),
                                                   "Could not find program with name '" + name + "'."))

        @staticmethod
        def FindProgram(name: str):
            return Namespace.Program(ExceptionIfNone(next([k for k in compiledPrograms if k.program.name == name]),
                                                     "Could not find program with name '" + name + "'."))

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

    # Compile the script
    exec(compiledProgram.script, globalsDict)

    existingParameters = compiledProgram.program.parameterValues.copy()
    newParameters: Dict[str, Any] = {}
    compiledProgram.parameterNames = {}
    # Extract and match parameters
    for symbol in compiledProgram.globals:
        parameter = compiledProgram.globals[symbol]
        if isinstance(parameter, ucscript.Parameter):
            if symbol in newParameters.keys():
                raise Exception("Parameter named '" + symbol + "' is already defined.")
            if symbol in existingParameters.keys():
                # Found a name match!
                value = existingParameters[symbol]
                del existingParameters[symbol]
                if IsTypeMatch(parameter.type, value):
                    # Type matches too!
                    newParameters[symbol] = value
                else:
                    # Type does not match
                    newParameters[symbol] = parameter.defaultValue
            else:
                # Name not found
                newParameters[symbol] = parameter.defaultValue
    compiledProgram.program.parameterValues = newParameters

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


def IsTypeMatch(t, value):
    if isinstance(t, type) and isinstance(value, t):
        return True
    if not isinstance(t, list):
        return False
    if len(t) == 1 and isinstance(t[0], type):
        if isinstance(value, list) and all([isinstance(v, t[0]) for v in value]):
            return True
        else:
            return False
    if len(t) >= 1 and all([isinstance(v, str) for v in value]):
        return True
    return False


def ExceptionIfNone(value, message):
    if value is None:
        raise Exception(message)
    return value
