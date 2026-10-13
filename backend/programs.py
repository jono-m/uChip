"""Compiling and running program scripts.

A CompiledProgram is built by executing a program's script. It holds the script's parameters,
functions and description, plus runtime state (running functions and log messages). The parameter
values themselves live on the chip's Program so they persist across recompiles and are saved.

Scripts use the API in ucscript.py, whose names are part of the scripting interface and are kept as is.
"""
import enum
import inspect
import time
import traceback
import types
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from backend import ucscript
from backend.chip import Chip, Program, Script, Valve
from backend.rig import Rig


class MessageKind(enum.Enum):
    LOG = 0
    RUNTIME_ERROR = 1
    COMPILE_ERROR = 2


@dataclass
class Message:
    text: str
    kind: MessageKind


@dataclass(eq=False)
class RunningFunction:
    """A function that yielded, and so is being run asynchronously by the run loop."""
    iterator: types.GeneratorType
    paused: bool = False
    yielded_value: Any = None
    # Time to resume execution (e.g. when WaitForSeconds is yielded), or None to step on the next tick.
    wake_time: Optional[float] = None


def _mtime(script: Script) -> Optional[float]:
    try:
        return script.file().stat().st_mtime
    except OSError:
        return None


_FINISHED = object()


@dataclass(eq=False)
class CompiledProgram:
    program: Program
    # What was compiled, used to detect when the program is out of date.
    script: Optional[Script] = None
    script_mtime: Optional[float] = None

    description: str = ""
    parameters: Dict[str, ucscript.Parameter] = field(default_factory=dict)
    functions: Dict[str, ucscript.ProgramFunction] = field(default_factory=dict)
    # Zero-argument functions that are shown as buttons.
    showable_functions: List[str] = field(default_factory=list)
    running: Dict[str, RunningFunction] = field(default_factory=dict)
    messages: List[Message] = field(default_factory=list)

    def is_out_of_date(self) -> bool:
        script = self.program.script
        return self.script != script or self.script_mtime != _mtime(script)

    def clear_messages(self):
        """Clears log and runtime error messages, keeping compile errors."""
        self.messages = [m for m in self.messages if m.kind == MessageKind.COMPILE_ERROR]

    def log_error(self, error: Exception, kind: MessageKind):
        text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        self.messages.append(Message(text, kind))

    # Running functions

    def call_function(self, symbol: str, *args, **kwargs):
        """Calls a program function. If it yields, it is registered to be run by the run loop."""
        if symbol in self.running:
            return  # Already running.
        if symbol not in self.functions:
            raise Exception("Could not find function '%s' in program '%s'" % (symbol, self.program.name))
        try:
            result = self.functions[symbol].function(*args, **kwargs)
        except Exception as e:
            self.log_error(e, MessageKind.RUNTIME_ERROR)
            return
        if isinstance(result, types.GeneratorType) and self.functions[symbol].canAsync:
            self.running[symbol] = RunningFunction(result)
        else:
            return result

    def tick_function(self, symbol: str, now: float):
        """Advances a running function by one step, unless it is paused or waiting."""
        running = self.running.get(symbol)
        if running is None or running.paused:
            return
        if running.wake_time is not None and now < running.wake_time:
            return
        try:
            running.yielded_value = next(running.iterator, _FINISHED)
            running.wake_time = _next_wake_time(running.wake_time, running.yielded_value, now)
        except Exception as e:
            self.log_error(e, MessageKind.RUNTIME_ERROR)
            self._end_function(symbol)
            return
        if running.yielded_value is _FINISHED:
            self._end_function(symbol)

    def stop_function(self, symbol: str):
        if symbol not in self.running:
            raise Exception("Could not find running function '%s' in program '%s'" % (symbol, self.program.name))
        self._end_function(symbol)

    def stop_all(self):
        for symbol in list(self.running):
            self._end_function(symbol)

    def _end_function(self, symbol: str):
        """Removes a running function and calls its onStop, logging any error it raises."""
        self.running.pop(symbol, None)
        try:
            self.functions[symbol].onStop()
        except Exception as e:
            self.log_error(e, MessageKind.RUNTIME_ERROR)

    def set_function_paused(self, symbol: str, paused: bool):
        if symbol not in self.running:
            raise Exception("Could not find running function '%s' in program '%s'" % (symbol, self.program.name))
        function = self.functions[symbol]
        function.onPause() if paused else function.onResume()
        self.running[symbol].paused = paused

    def is_function_async(self, symbol: str) -> bool:
        """Whether calling the function starts a run that can be paused and stopped (it yields)."""
        function = self.functions[symbol]
        return function.canAsync and inspect.isgeneratorfunction(function.function)

    def is_function_running(self, symbol: str) -> bool:
        return symbol in self.running

    def is_function_paused(self, symbol: str) -> bool:
        return symbol in self.running and self.running[symbol].paused

    def tick(self, now: Optional[float] = None, on_function_start: Callable[[str], None] = lambda symbol: None):
        """Advances every running function by one step."""
        now = time.perf_counter() if now is None else now
        for symbol in list(self.running):
            on_function_start(symbol)
            self.tick_function(symbol, now)


def _next_wake_time(wake_time: Optional[float], yielded_value, now: float) -> Optional[float]:
    """When a function that just yielded [yielded_value] should next be stepped.

    A wait is counted from when the previous wait was due rather than from [now] (a little later, at the
    tick that stepped the function), so consecutive waits don't drift. If the function has fallen a whole
    wait behind (e.g. it was paused or the run loop stalled), it is counted from [now] instead, rather
    than stepping it on every tick to catch up.
    """
    if not isinstance(yielded_value, ucscript.WaitForSeconds):
        return None
    next_wake_time = (now if wake_time is None else wake_time) + yielded_value.seconds
    return next_wake_time if next_wake_time > now else now + yielded_value.seconds


# Compilation

def _build_environment() -> dict:
    """A globals dictionary with built-ins, where 'import ucscript' gives our ucscript module."""
    globals_dict = {}
    exec("", globals_dict)
    builtins = globals_dict["__builtins__"].copy()
    builtin_import = builtins["__import__"]

    def import_interceptor(name, *args, **kwargs):
        if name == "ucscript":
            return ucscript
        return builtin_import(name, *args, **kwargs)

    builtins["__import__"] = import_interceptor
    globals_dict["__builtins__"] = builtins
    return globals_dict


def compile_program(program: Program, chip: Chip, rig: Rig,
                    get_compiled: Callable[[Program], CompiledProgram]) -> CompiledProgram:
    """Executes [program]'s script and binds it to [chip] and [rig]. Errors are logged, not raised.

    [get_compiled] looks up the compiled form of other programs (for FindProgram and Program parameters).
    """
    compiled = CompiledProgram(program, script=program.script, script_mtime=_mtime(program.script))
    try:
        source = "from ucscript import *\n" + program.script.read()
        globals_dict = _build_environment()
        exec(source, globals_dict)
        _extract_symbols(globals_dict, compiled)
        _match_parameter_values(compiled)
        _attach_environment(globals_dict, compiled, chip, rig, get_compiled)
    except Exception as e:
        compiled.log_error(e, MessageKind.COMPILE_ERROR)
    return compiled


def _extract_symbols(globals_dict: dict, compiled: CompiledProgram):
    for symbol, value in globals_dict.items():
        if isinstance(value, ucscript.Parameter):
            compiled.parameters[symbol] = value
        elif isinstance(value, ucscript.SetDescription):
            compiled.description = value.description
        elif isinstance(value, ucscript.ProgramFunction):
            compiled.functions[symbol] = value
        elif inspect.isfunction(value):
            compiled.functions[symbol] = ucscript.ProgramFunction(value)
    compiled.showable_functions = [symbol for symbol, f in compiled.functions.items()
                                   if len(inspect.signature(f.function).parameters) == 0 and not f.hidden]
    for symbol, parameter in compiled.parameters.items():
        if parameter.displayName is None:
            parameter.displayName = symbol
    for symbol, function in compiled.functions.items():
        if function.functionName is None:
            function.functionName = symbol


def _match_parameter_values(compiled: CompiledProgram):
    """Keeps stored values that still fit their parameter's type and resets the rest."""
    program = compiled.program
    values, visibility = {}, {}
    for symbol, parameter in compiled.parameters.items():
        if symbol in program.parameter_values and \
                does_value_match_type(program.parameter_values[symbol], parameter.parameterType):
            values[symbol] = program.parameter_values[symbol]
            visibility[symbol] = program.parameter_visibility.get(symbol, True)
        else:
            values[symbol] = default_value(parameter)
            visibility[symbol] = True
    program.parameter_values = values
    program.parameter_visibility = visibility


def _attach_environment(globals_dict: dict, compiled: CompiledProgram, chip: Chip, rig: Rig,
                        get_compiled: Callable[[Program], CompiledProgram]):
    """Binds the script's Parameter, ProgramFunction, FindValve, FindProgram and Log to uChip."""

    def script_valve(valve: Valve) -> ucscript.Valve:
        v = ucscript.Valve()
        v.IsOpen = lambda: rig.get_solenoid(valve.solenoid)
        v.SetOpen = lambda state: rig.set_solenoid(valve.solenoid, bool(state))
        v.SetSolenoidNumber = lambda number: setattr(valve, "solenoid", number)
        v.SetName = lambda name: setattr(valve, "name", name)
        v.Name = lambda: valve.name
        v.SolenoidNumber = lambda: valve.solenoid
        return v

    def script_program(program: Program) -> ucscript.Program:
        p = ucscript.Program()
        other = get_compiled(program)
        p.__dict__.update(other.functions)
        p.__dict__.update(other.parameters)
        p.Name = lambda: program.name
        p.SetName = lambda name: setattr(program, "name", name)
        return p

    def to_script_value(value):
        if isinstance(value, Valve):
            return script_valve(value)
        if isinstance(value, Program):
            return script_program(value)
        if isinstance(value, list):
            return [to_script_value(v) for v in value]
        return value

    def bind_parameter(symbol: str, parameter: ucscript.Parameter):
        def set_value(value):
            if not does_value_match_type(value, parameter.parameterType):
                raise Exception("Value did not match type of parameter '%s' (%s)" % (
                    symbol, str(parameter.parameterType)))
            compiled.program.parameter_values[symbol] = value

        parameter.Get = lambda: to_script_value(compiled.program.parameter_values[symbol])
        parameter.Set = set_value

    def bind_function(symbol: str, function: ucscript.ProgramFunction):
        function.Call = lambda *args, **kwargs: compiled.call_function(symbol, *args, **kwargs)
        function.IsPaused = lambda: compiled.is_function_paused(symbol)
        function.Stop = lambda: compiled.stop_function(symbol)
        function.Resume = lambda: compiled.set_function_paused(symbol, False)
        function.Pause = lambda: compiled.set_function_paused(symbol, True)
        function.IsRunning = lambda: compiled.is_function_running(symbol)

    for symbol, parameter in compiled.parameters.items():
        if not is_type_valid(parameter.parameterType):
            raise Exception("Parameter type is not valid! Displayable parameters can be: "
                            "bool, int, float, str, Valve, Program, List(type), or Options(str1, str2...)")
        bind_parameter(symbol, parameter)

    for symbol, function in compiled.functions.items():
        bind_function(symbol, function)

    def find_valve(name: str):
        valve = next((v for v in chip.valves if v.name == name), None)
        if valve is None:
            raise Exception("Could not find a valve named '%s'." % name)
        return script_valve(valve)

    def find_program(name: str):
        program = next((p for p in chip.programs if p.name == name), None)
        if program is None:
            raise Exception("Could not find a program named '%s'." % name)
        return script_program(program)

    globals_dict["FindValve"] = find_valve
    globals_dict["FindProgram"] = find_program
    globals_dict["Log"] = lambda text: compiled.messages.append(Message(str(text), MessageKind.LOG))


# Parameter types

def default_value_for_type(t):
    if t == bool:
        return False
    if t == int:
        return 0
    if t == float:
        return 0.0
    if t == str:
        return ""
    if isinstance(t, ucscript.OptionsParameterType):
        return t.options[0]
    if isinstance(t, ucscript.ListParameterType):
        return []
    return None  # Valve and Program: none chosen.


def default_value(parameter: ucscript.Parameter):
    """A new value for [parameter]: its defaultValue if that fits its type (for an options parameter, an
    option or an option's index), otherwise the type's default, kept within its minimum and maximum."""
    t, value = parameter.parameterType, parameter.defaultValue
    is_index = isinstance(value, int) and not isinstance(value, bool)
    if isinstance(t, ucscript.OptionsParameterType) and is_index and 0 <= value < len(t.options):
        value = t.options[value]
    if value is None or not does_value_match_type(value, t):
        value = default_value_for_type(t)
    if t in (int, float) and value is not None:
        if parameter.minimum is not None and value < parameter.minimum:
            value = parameter.minimum
        if parameter.maximum is not None and value > parameter.maximum:
            value = parameter.maximum
        value = t(value)
    return value


def is_type_valid(t) -> bool:
    return t in [float, int, str, bool, ucscript.Valve, ucscript.Program] or \
        is_options_type(t) or is_list_type(t)


def is_options_type(t) -> bool:
    return isinstance(t, ucscript.OptionsParameterType) and len(t.options) > 0 and \
        all(isinstance(x, str) for x in t.options)


def is_list_type(t) -> bool:
    return isinstance(t, ucscript.ListParameterType) and is_type_valid(t.listType)


def do_types_match(t1, t2) -> bool:
    if isinstance(t1, type) and isinstance(t2, type):
        return t1 == t2
    if isinstance(t1, ucscript.ListParameterType) and isinstance(t2, ucscript.ListParameterType):
        return do_types_match(t1.listType, t2.listType)
    if isinstance(t1, ucscript.OptionsParameterType) and isinstance(t2, ucscript.OptionsParameterType):
        return t1.options == t2.options
    return False


def does_value_match_type(value, t) -> bool:
    """Whether [value] can be stored for a parameter of type [t]. An int is accepted as a float."""
    if t == bool:
        return isinstance(value, bool)
    if t == int:
        return isinstance(value, int) and not isinstance(value, bool)
    if t == float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if t == str:
        return isinstance(value, str)
    if t == ucscript.Valve:
        return isinstance(value, Valve)
    if t == ucscript.Program:
        return isinstance(value, Program)
    if isinstance(t, ucscript.ListParameterType):
        return isinstance(value, list) and all(does_value_match_type(v, t.listType) for v in value)
    if isinstance(t, ucscript.OptionsParameterType):
        return isinstance(value, str) and value in t.options
    return False
