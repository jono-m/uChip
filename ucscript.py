# ucscript.py
# This file should be imported by any uChip scripts.
import typing
from typing import Any, Callable, Union


class Parameter:
    """Used to declare global parameters for a script. Parameter objects must be declared on the
    global scope of the script to be recognized by uChip."""

    def __init__(self, parameterType, displayName=None, defaultValue=None, minimum=None,
                 maximum=None):
        """Create a Parameter object for a given type, with optional display name and range for
        numeric types.

        Keyword arguments:
            parameterType -- A uChip-compatible type (e.g. int, float, str, OptionsParameter,
                             ListParameter, Valve, Program).
            displayName -- A string. If specified, override the parameter's display name.
            defaultValue -- If specified, initialize the parameter with this value.
            minimum/maximum -- If specified, set a minimum or maximum value for numeric parameters.
        """
        self.parameterType = parameterType
        self.defaultValue = defaultValue
        self.displayName = displayName
        self.minimum = minimum
        self.maximum = maximum


    def Set(self, value):
        """Set the parameter to a given value."""
        pass

    def Get(self) -> Any:
        """Get the current parameter value."""
        pass

# A Valve object should not be instantiated by itself. Valves can be retrieved by name with
# FindValve(name), or passed through the GUI with Parameter(Valve).
class Valve:
    def SetOpen(self, state: bool):
        pass

    def Open(self):
        self.SetOpen(True)

    def Close(self):
        self.SetOpen(False)

    def IsOpen(self) -> bool:
        pass

    def IsClosed(self):
        return not self.IsOpen()

    def Name(self) -> str:
        pass

    def SetName(self, name: str):
        pass

    def SolenoidNumber(self) -> int:
        pass

    def SetSolenoidNumber(self, number: int):
        pass


# A Program object should not be instantiated by itself. Programs can be retrieved by name with
# FindProgram(name) or passed through the GUI with Parameter(Program). All of the program's
# parameters and functions are accessible through this object by their symbol name.
class Program:
    def Name(self) -> str:
        pass

    def SetName(self, name: str):
        pass


# Program functions are wrapped in a ProgramFunction object. This object can be called as normal
# to run the function but, if a value is yielded, the function will be run asynchronously. If the
# function yields a value but you want it to NOT run asynchronously, the @nonAsync decorator should
# be used.
class ProgramFunction:
    def __init__(self, function: Callable):
        self.functionName: typing.Optional[str] = None
        self.function = function
        self.canAsync = True
        self.onStop: typing.Optional[Callable] = lambda: None
        self.onPause: typing.Optional[Callable] = lambda: None
        self.onResume: typing.Optional[Callable] = lambda: None
        self.hidden = False

    def __call__(self, *args, **kwargs):
        return self.Call(*args, **kwargs)

    def Call(self, *args, **kwargs):
        raise NotImplementedError("ERROR!")

    def IsRunning(self) -> bool:
        pass

    def IsPaused(self) -> bool:
        pass

    def Pause(self):
        pass

    def Stop(self):
        pass

    def Resume(self):
        pass


# The following values can be yielded by program functions to pause program execution for a given
# amount of time.
# e.g. yield WaitForSeconds(5)
class WaitForSeconds:
    def __init__(self, seconds: float):
        self.seconds = seconds


class WaitForMinutes(WaitForSeconds):
    def __init__(self, minutes):
        super().__init__(60 * minutes)


class WaitForHours(WaitForSeconds):
    def __init__(self, hours):
        super().__init__(60 * 60 * hours)


class OptionsParameter:
    def __init__(self, *args):
        self.options = args


class ListParameter:
    def __init__(self, listType):
        self.listType = listType


def _pf(f):
    return f if isinstance(f, ProgramFunction) else ProgramFunction(f)


# A decorator that sets the function name to [fName]
# e.g. @functionName("Rinse Valves")
def functionName(fName: str):
    def decorate(function: Union[Callable, ProgramFunction]):
        f = _pf(function)
        f.functionName = fName
        return f

    return decorate


# A decorator that forces the function to not execute asynchronously EVER.
# e.g. @nonAsync
def nonAsync(function: Union[Callable, ProgramFunction]):
    f = _pf(function)
    f.canAsync = False
    return f


# A decorator that forces the function to not show in the program item list
# e.g. @hidden
def hidden(function: Union[Callable, ProgramFunction]):
    f = _pf(function)
    f.hidden = True
    return f


# A decorator that calls a function once the decorated asynchronous function is stopped.
def onStop(funcToCall: typing.Callable):
    def decorate(function: Union[Callable, ProgramFunction]):
        f = _pf(function)
        f.onStop = funcToCall
        return f

    return decorate


# A decorator that calls a function once the decorated asynchronous function is paused.
def onPause(funcToCall: typing.Callable):
    def decorate(function: Union[Callable, ProgramFunction]):
        f = _pf(function)
        f.onPause = funcToCall
        return f

    return decorate


# A decorator that calls a function once the decorated asynchronous function is resumed.
def onResume(funcToCall: typing.Callable):
    def decorate(function: Union[Callable, ProgramFunction]):
        f = _pf(function)
        f.onResume = funcToCall
        return f

    return decorate


# Sets the program description.
class SetDescription:
    def __init__(self, description: str):
        self.description = description


# Finds a valve in the chip project named [name].
def FindValve(name: str) -> Valve:
    pass


# Finds a program in the chip project named [name].
def FindProgram(name: str) -> Program:
    pass


# Logs text to the program output.
def Log(text: str):
    pass
