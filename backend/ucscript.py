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


class Valve:
    """A valve on the chip. Don't create one yourself: get it with FindValve(name), or let the user
    pick one with Parameter(Valve)."""

    def SetOpen(self, state: bool):
        """Opens the valve if [state] is True, otherwise closes it."""
        pass

    def Open(self):
        """Opens the valve."""
        self.SetOpen(True)

    def Close(self):
        """Closes the valve."""
        self.SetOpen(False)

    def IsOpen(self) -> bool:
        """Whether the valve is open."""
        pass

    def IsClosed(self):
        """Whether the valve is closed."""
        return not self.IsOpen()

    def Name(self) -> str:
        """The valve's name."""
        pass

    def SetName(self, name: str):
        """Renames the valve."""
        pass

    def SolenoidNumber(self) -> int:
        """The solenoid number that drives the valve."""
        pass

    def SetSolenoidNumber(self, number: int):
        """Changes the solenoid number that drives the valve."""
        pass


class Program:
    """Another program on the chip. Don't create one yourself: get it with FindProgram(name), or let
    the user pick one with Parameter(Program). The program's parameters and functions are available
    as attributes by their names in its script, e.g. pump.RunPump() or pump.cyclesPerSecond.Set(2)."""

    def Name(self) -> str:
        """The program's name."""
        pass

    def SetName(self, name: str):
        """Renames the program."""
        pass


class ProgramFunction:
    """A function in a program's script. Call it as normal to run it. A function that yields (e.g.
    yield WaitForSeconds(1)) runs in the background, and can be paused, resumed and stopped."""

    def __init__(self, function: Callable):
        self.functionName: typing.Optional[str] = None
        self.function = function
        self.canAsync = True
        self.onStop: typing.Optional[Callable] = lambda: None
        self.onPause: typing.Optional[Callable] = lambda: None
        self.onResume: typing.Optional[Callable] = lambda: None
        self.hidden = True

    def __call__(self, *args, **kwargs):
        return self.Call(*args, **kwargs)

    def Call(self, *args, **kwargs):
        raise NotImplementedError("ERROR!")

    def IsRunning(self) -> bool:
        """Whether the function is running in the background."""
        pass

    def IsPaused(self) -> bool:
        """Whether the function is paused."""
        pass

    def Pause(self):
        """Pauses the running function."""
        pass

    def Stop(self):
        """Stops the running function."""
        pass

    def Resume(self):
        """Resumes the paused function."""
        pass


class WaitForSeconds:
    """Yield this from a function to wait, e.g. yield WaitForSeconds(5). Other functions keep running."""

    def __init__(self, seconds: float):
        self.seconds = seconds


class WaitForMinutes(WaitForSeconds):
    """Yield this from a function to wait, e.g. yield WaitForMinutes(2)."""

    def __init__(self, minutes):
        super().__init__(60 * minutes)


class WaitForHours(WaitForSeconds):
    """Yield this from a function to wait, e.g. yield WaitForHours(1)."""

    def __init__(self, hours):
        super().__init__(60 * 60 * hours)


class OptionsParameterType:
    def __init__(self, options: typing.List[str]):
        self.options = options


class OptionsParameter(Parameter):
    """A parameter chosen from a dropdown of [options]. Get() returns the chosen option's text."""

    def __init__(self, options: typing.List[str], displayName=None, defaultIndex=0):
        super().__init__(OptionsParameterType(options), displayName, defaultIndex)


class ListParameterType:
    def __init__(self, listType):
        self.listType = listType


class ListParameter(Parameter):
    """A parameter holding a list of values of [listType], e.g. ListParameter(Valve)."""

    def __init__(self, listType: typing.Type, displayName=None):
        super().__init__(ListParameterType(listType), displayName)


def _pf(f):
    return f if isinstance(f, ProgramFunction) else ProgramFunction(f)


def display(displayName):
    """Decorator that shows a zero-argument function as a button on the program. Use @display, or
    @display("Button name") to change the button's text."""
    def GenerateDecorator(function: Union[Callable, ProgramFunction]):
        f = _pf(function)
        if displayName is not None:
            f.functionName = displayName
        f.hidden = False
        return f

    if callable(displayName):
        func = displayName
        displayName = None
        return GenerateDecorator(func)
    return GenerateDecorator


def onStop(funcToCall: typing.Callable):
    """Decorator that calls [funcToCall] when the decorated background function stops or finishes."""
    def Inner(function: Union[Callable, ProgramFunction]):
        f = _pf(function)
        f.onStop = funcToCall
        return f
    return Inner


def onPause(funcToCall: typing.Callable):
    """Decorator that calls [funcToCall] when the decorated background function is paused."""
    def decorate(function: Union[Callable, ProgramFunction]):
        f = _pf(function)
        f.onPause = funcToCall
        return f

    return decorate


def onResume(funcToCall: typing.Callable):
    """Decorator that calls [funcToCall] when the decorated background function is resumed."""
    def decorate(function: Union[Callable, ProgramFunction]):
        f = _pf(function)
        f.onResume = funcToCall
        return f

    return decorate


class SetDescription:
    """Sets the description shown in the program's inspector, e.g. SetDescription("Runs the pump.")"""

    def __init__(self, description: str):
        self.description = description


def FindValve(name: str) -> Valve:
    """The valve on the chip named [name]."""
    pass


def FindProgram(name: str) -> Program:
    """The program on the chip named [name]."""
    pass


def Log(text: str):
    """Shows [text] in the program's log."""
    pass
