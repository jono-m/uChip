import pathlib
import time
import types
import typing

import ucscript
from typing import Optional, List, Dict, Any
import Data.Chip as Chip
from Data.Rig import Rig
import inspect


# A compiled program is built from a script and extracts parameters, functions and the description
# from the script. The parameter values are instead stored in the chip program, as these values
# should be persisted across recompilation and saved to the project file.
class CompiledProgram:
    def __init__(self, program: Chip.Program):
        # The chip script that this instance was compiled from.
        self.program = program

        # The path to the script file used for compilation and the time of last modification. This
        # is used to automatically recompile when out-of-date.
        self.compiledPath: Optional[pathlib.Path] = None
        self.lastModTime: Optional[float] = None

        # The description from the compiled program.
        self.description = ""

        # The parameters and functions from the compiled program, mapped by symbols.
        self.parameters: Dict[str, ucscript.Parameter] = {}
        self.programFunctions: Dict[str, ucscript.ProgramFunction] = {}

        # Zero argument functions are important becase they can be run through GUI buttons.
        self.showableFunctions: List[str] = []

        # Message queue and any fatal error message.
        self.messages: List[str] = []

        # Zero-argument functions can be run by button press. Functions that yield values will
        # be run asynchronously and are stored in this dictionary.
        self.asyncFunctions: Dict[str, CompiledProgram.AsyncFunctionInfo] = {}

    # Details of asynchronous functions
    class AsyncFunctionInfo:
        def __init__(self, iterator: types.GeneratorType):
            # The function can be paused/resumed.
            self.paused = False

            # Stores the iterator returned from the function.
            self.iterator = iterator

            # Stores the yielded value from the last iteration.
            self.yieldedValue = None

            # The time of the last iteration.
            self.lastIterationTime = None


# Returns 'True' if the compiled program is out-of-date.
def IsOutOfDate(compiledProgram: CompiledProgram):
    return compiledProgram.compiledPath != compiledProgram.program.path or \
           compiledProgram.lastModTime != compiledProgram.program.path.stat().st_mtime


# Builds an environment with built-ins as well as an import interceptor to pass along the correct
# ucscript file when imported.
def BuildEnvironment():
    # Grab builtins
    globalsDict = {}
    exec("", globalsDict)
    globalsDict = globalsDict.copy()

    # The built-in importer
    builtInImporter = globalsDict['__builtins__']['__import__']

    # A replacement for the importer that passes along ucscript.py when needed.
    def ImportInterceptor(name, *args, **kwargs):
        if name == "ucscript":
            return ucscript
        else:
            return builtInImporter(name, *args, **kwargs)

    # Replace the importer
    globalsDict['__builtins__'] = globalsDict['__builtins__'].copy()
    globalsDict['__builtins__']['__import__'] = ImportInterceptor
    return globalsDict


# Recompiles a CompiledProgram object (which must have a Chip.Program already attached.
def Recompile(compiledProgram: CompiledProgram, chip: Chip, rig: Rig,
              programList: List[CompiledProgram]) -> CompiledProgram:
    try:
        program = compiledProgram.program
        scriptFile = open(program.path, "r")
        script = scriptFile.read()
        scriptFile.close()

        CompiledProgram.__init__(compiledProgram, program)
        compiledProgram.lastModTime = program.path.stat().st_mtime
        compiledProgram.compiledPath = program.path.absolute()

        globalsDict = BuildEnvironment()
        # Compile the script. The globals dictionary will have everything that resulted from
        # compilation.
        exec(script, globalsDict)
        # We can then extract symbols from the dictionary and validate them.
        ExtractSymbols(globalsDict, compiledProgram)
        MatchParameterValues(compiledProgram)
        AttachEnvironment(globalsDict, compiledProgram, chip, rig, programList)
    except Exception as e:
        compiledProgram.messages.append(repr(e.with_traceback(e.__traceback__)))
    return compiledProgram


# Sort symbols from the compiled global dictionary into the CompiledProgram symbol dictionaries.
def ExtractSymbols(globalsDict: Dict, compiledProgram: CompiledProgram):
    for symbol in globalsDict:
        value = globalsDict[symbol]
        if isinstance(value, ucscript.Parameter):
            compiledProgram.parameters[symbol] = value
        elif isinstance(value, ucscript.SetDescription):
            compiledProgram.description = value.description
        elif isinstance(value, ucscript.ProgramFunction):
            compiledProgram.programFunctions[symbol] = value
        elif inspect.isfunction(value):
            compiledProgram.programFunctions[symbol] = ucscript.ProgramFunction(value)
    compiledProgram.showableFunctions = [x for x, f in compiledProgram.programFunctions.items() if
                                         len(inspect.signature(
                                             f.function).parameters) == 0 and not f.hidden]

    for parameterSymbol in compiledProgram.parameters:
        if compiledProgram.parameters[parameterSymbol].displayName is None:
            # TODO: beautify symbol
            compiledProgram.parameters[parameterSymbol].displayName = parameterSymbol
    for functionSymbol in compiledProgram.programFunctions:
        if compiledProgram.programFunctions[functionSymbol].functionName is None:
            # TODO: beautify symbol
            compiledProgram.programFunctions[functionSymbol].functionName = functionSymbol


# Make sure that the program parameter values dictionary has the appropriate fields.
def MatchParameterValues(compiledProgram: CompiledProgram):
    newValueDict = {}
    newVisibilityDict = {}
    for symbol, parameter in compiledProgram.parameters.items():
        if symbol in compiledProgram.program.parameterValues:
            if DoesValueMatchType(compiledProgram.program.parameterValues[symbol],
                                  parameter.parameterType):
                newValueDict[symbol] = compiledProgram.program.parameterValues[symbol]
                newVisibilityDict[symbol] = compiledProgram.program.parameterVisibility[symbol]
                continue
        newValueDict[symbol] = NoneValueForType(parameter.parameterType)
        newVisibilityDict[symbol] = True
    compiledProgram.program.parameterValues = newValueDict
    compiledProgram.program.parameterVisibility = newVisibilityDict


# Binds the following elements of the uChip script to the current uChip environment:
#   - Get() and Set() methods of all Parameter objects
#   - Asynchronous calling and Stop/Pause methods for all ProgramFunction objects
#   - FindValve() and FindProgram()
def AttachEnvironment(globalsDict: Dict, compiledProgram: CompiledProgram, chip: Chip, rig: Rig,
                      compiledProgramList: List[CompiledProgram]):
    # When FindValve() or Parameter.Get() is used to get a ucscript.Valve object, it must be bound
    # to the rig and the underlying Valve object.
    def BuildUCSValve(valve: Chip.Valve):
        v = ucscript.Valve()
        v.IsOpen = lambda: rig.GetSolenoidState(valve.solenoidNumber)
        v.SetOpen = lambda x: rig.SetSolenoidState(valve.solenoidNumber, bool(x))

        def SetSolenoidNumber(x):
            valve.solenoidNumber = x

        def SetName(x):
            valve.name = x

        v.SetSolenoidNumber = SetSolenoidNumber
        v.SetName = SetName
        v.Name = lambda: valve.name
        v.SolenoidNumber = lambda: valve.solenoidNumber
        return v

    # When FindProgram() or Parameter.Get() is used to get a ucscript.Program object, it must be
    # bound to the functions and parameters that are bound to the uChip environment.
    def BuildUCSProgram(program: Chip.Program):
        p = ucscript.Program()
        cp = next([x for x in compiledProgramList if x.program == program], None)
        for fs in cp.programFunctions:
            p.__dict__[fs] = cp.programFunctions[fs]
        for ps in cp.parameters:
            p.__dict__[ps] = cp.parameters[ps]
        p.Name = lambda: program.name

        def SetName(x):
            program.name = x

        p.SetName = SetName
        return p

    # Binds a parameter to the uChip environment (Set(value) and Get() methods).
    def BindParameter(symbol: str):
        p = compiledProgram.parameters[symbol]

        def GetParameterValue():
            value = compiledProgram.program.parameterValues[symbol]

            def Prepare(v):
                if isinstance(v, Chip.Valve):
                    return BuildUCSValve(v)
                if isinstance(v, Chip.Program):
                    return BuildUCSProgram(v)
                if isinstance(v, list):
                    return [Prepare(lv) for lv in v]
                return v

            return Prepare(value)

        def SetParameterValue(value: Any):
            if not DoesValueMatchType(value, p.parameterType):
                raise Exception("Value did not match type of parameter '%s' (%s)" % (
                    parameterSymbol, str(p.parameterType)))
            compiledProgram.program.parameterValues[parameterSymbol] = value

        p.Get = GetParameterValue
        p.Set = SetParameterValue

    # Binds a function to the uChip environment.
    def BindFunction(symbol: str):
        def callOverride(*args, **kwargs):
            return CallFunction(compiledProgram, symbol, *args, **kwargs)

        programFunction = compiledProgram.programFunctions[symbol]
        programFunction.Call = callOverride
        programFunction.IsPaused = lambda: IsFunctionPaused(compiledProgram, symbol)
        programFunction.Stop = lambda: StopFunction(compiledProgram, symbol)
        programFunction.Resume = lambda: SetFunctionPaused(compiledProgram, symbol, False)
        programFunction.Pause = lambda: SetFunctionPaused(compiledProgram, symbol, True)
        programFunction.IsRunning = lambda: IsFunctionRunning(compiledProgram, symbol)

    # Bind parameters to the uChip environment.
    for parameterSymbol, parameter in compiledProgram.parameters.items():
        if not IsTypeValid(parameter.parameterType):
            raise Exception(
                "Parameter type is not valid! Displayable parameters can be: "
                "bool, int, float, str, Valve, Program, List(type), or Options(str1, str2...)")
        BindParameter(parameterSymbol)

    # Bind functions to the uChip environment.
    for functionSymbol in compiledProgram.programFunctions:
        BindFunction(functionSymbol)

    # Bind the FindValve and FindProgram global methods to the uChip environment.
    def FindValveInChip(name: str):
        valve = ExceptionIfNone(next([x for x in chip.valves if x.name == name], None),
                                "Could not find a valve named '%s'." % name)
        return BuildUCSValve(valve)

    def FindProgramInChip(name: str):
        program = ExceptionIfNone(next([x for x in chip.programs if x.name == name], None),
                                  "Could not find a program named '%s'." % name)
        return BuildUCSProgram(program)

    globalsDict['FindValve'] = FindValveInChip
    globalsDict['FindProgram'] = FindProgramInChip


# Calls a function named [functionSymbol] in [compiledProgram]. This is often called by the GUI when
# a program button is clicked, but functions can also be called by a UCS program indirectly via
# FindProgram() or Parameter.Get().
def CallFunction(compiledProgram: CompiledProgram, functionSymbol: str, *fargs, **fkwargs):
    if functionSymbol in compiledProgram.asyncFunctions:
        # Function is already running!
        return
    if functionSymbol not in compiledProgram.programFunctions:
        raise Exception("Could not find function '%s' in program '%s'" %
                        (functionSymbol, compiledProgram.program.name))
    function = compiledProgram.programFunctions[functionSymbol].function
    try:
        returnValue = function(*fargs, **fkwargs)
    except Exception as e:
        compiledProgram.messages.append(str(e))
        return
    if isinstance(returnValue, types.GeneratorType) and \
            compiledProgram.programFunctions[functionSymbol].canAsync:
        newRunning = CompiledProgram.AsyncFunctionInfo(returnValue)
        compiledProgram.asyncFunctions[functionSymbol] = newRunning
    else:
        return returnValue


def TickFunction(compiledProgram: CompiledProgram, functionSymbol: str):
    if functionSymbol not in compiledProgram.asyncFunctions:
        return

    functionInfo = compiledProgram.asyncFunctions[functionSymbol]

    class FinishedIndicator:
        pass

    FinishedIndicator = FinishedIndicator()
    if functionInfo.paused:
        return
    if isinstance(functionInfo.yieldedValue, ucscript.WaitForSeconds):
        if time.time() - functionInfo.lastIterationTime < functionInfo.yieldedValue.seconds:
            return
    try:
        functionInfo.yieldedValue = next(functionInfo.iterator, FinishedIndicator)
        functionInfo.lastIterationTime = time.time()
    except Exception as e:
        compiledProgram.messages.append(str(e))
        StopFunction(compiledProgram, functionSymbol)
        return
    compiledProgram.lastCallTime = time.time()
    if functionInfo.yieldedValue is FinishedIndicator:
        del compiledProgram.asyncFunctions[functionSymbol]


def StopFunction(compiledProgram: CompiledProgram, functionSymbol: str):
    if functionSymbol not in compiledProgram.asyncFunctions:
        raise Exception("Could not find running function '%s' in program '%s'" %
                        (functionSymbol, compiledProgram.program.name))
    compiledProgram.programFunctions[functionSymbol].onStop()
    del compiledProgram.asyncFunctions[functionSymbol]


def SetFunctionPaused(compiledProgram: CompiledProgram, functionSymbol: str, paused: bool):
    if functionSymbol not in compiledProgram.asyncFunctions:
        raise Exception("Could not find running function '%s' in program '%s'" %
                        (functionSymbol, compiledProgram.program.name))
    compiledProgram.programFunctions[functionSymbol].onPause() if paused else \
        compiledProgram.programFunctions[functionSymbol].onResume()
    compiledProgram.asyncFunctions[functionSymbol].paused = paused


def IsFunctionRunning(compiledProgram: CompiledProgram, functionSymbol: str):
    return functionSymbol in compiledProgram.asyncFunctions


def IsFunctionPaused(compiledProgram: CompiledProgram, functionSymbol: str):
    return IsFunctionRunning(compiledProgram, functionSymbol) and \
           compiledProgram.asyncFunctions[functionSymbol].paused


def NoneValueForType(t):
    if t == int:
        return 0
    if t == float:
        return 0.0
    if t == str:
        return ""
    if isinstance(t, ucscript.OptionsParameter):
        return t.options[0]
    if isinstance(t, ucscript.ListParameter):
        return []


def IsTypeValid(parameterType):
    return (parameterType in [float, int, str, bool, ucscript.Valve, ucscript.Program]) or \
           IsTypeValidOptions(parameterType) or IsTypeValidList(parameterType)


# Helper method for if the parameter is an enum (a list of strings)
def IsTypeValidOptions(parameterType):
    return isinstance(parameterType, ucscript.OptionsParameter) and len(
        parameterType.options) > 0 and all([isinstance(x, str) for x in parameterType.options])


# Helper method for if the parameter is a list of displayable parameters
def IsTypeValidList(parameterType):
    return isinstance(parameterType, ucscript.ListParameter) and IsTypeValid(parameterType.listType)


def DoTypesMatch(t1, t2):
    if isinstance(t1, type) and isinstance(t2, type):
        return t1 == t2
    if isinstance(t1, ucscript.ListParameter) and isinstance(t2, ucscript.ListParameter):
        return DoTypesMatch(t1.listType, t2.listType)
    if isinstance(t1, ucscript.OptionsParameter) and isinstance(t2, ucscript.OptionsParameter):
        return t1.options == t2.options
    return False


def DoesValueMatchType(value, t):
    if isinstance(t, type) and isinstance(value, t):
        return True
    if isinstance(value, Chip.Valve) and t == ucscript.Valve or \
            isinstance(value, Chip.Program) and t == ucscript.Program:
        return True
    if isinstance(value, list) and isinstance(t, ucscript.ListParameter):
        return [DoesValueMatchType(v, t.listType) for v in value]
    if isinstance(value, str) and isinstance(t, ucscript.OptionsParameter):
        return value in t.options


def ExceptionIfNone(value, message):
    if value is None:
        raise Exception(message)
    return value
