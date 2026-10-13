"""Runs the programs of a session's chip.

The runner holds the compiled form of each program on the chip, including its running functions.
Each tick runs posted commands, advances every running function by one step, then sends the solenoid
states to the rig, so valve changes go out in the same tick. Times are on the time.perf_counter() clock.
The GUI ticks it about once a millisecond on a QThread (gui/runner_thread.py); a test can call tick()
itself.

Other threads change program state (calling, pausing or stopping functions) by posting a command,
which the next tick runs, rather than directly, so a tick never sees that state change halfway.

Compiled programs whose program is no longer on the session's chip (because it was removed, or
another chip was opened) are dropped on the next tick, and their running functions are stopped (calling
their onStop). So are those of a program recompiled because its script changed.

A function that blocks (e.g. an infinite loop without a yield) stalls the loop; stuck_function()
reports that.
"""
import queue
import time
import traceback
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Tuple

from backend.chip import Program
from backend.programs import CompiledProgram, compile_program
from backend.session import Session


@dataclass(eq=False)
class Runner:
    session: Session
    compiled_program_map: Dict[Program, CompiledProgram] = field(default_factory=dict)
    interval: float = 0.001
    command_queue: queue.SimpleQueue = field(default_factory=queue.SimpleQueue)
    last_error: Optional[str] = None
    # The function currently being ticked (or the command being run), and when it started.
    tick_started: Optional[float] = None
    tick_program_name: str = ""
    tick_function: str = ""

    def get_compiled_program(self, program: Program) -> CompiledProgram:
        """The compiled form of [program], (re)compiling it if its script has changed."""
        compiled = self.compiled_program_map.get(program)
        if compiled is None or compiled.is_out_of_date():
            if compiled is not None:
                compiled.stop_all()
            compiled = compile_program(program, self.session.chip, self.session.rig, self.get_compiled_program)
            self.compiled_program_map[program] = compiled
        return compiled

    def ensure_programs_compiled(self):
        for program in self.session.chip.programs:
            self.get_compiled_program(program)

    def enqueue_command(self, command: Callable[[], None], program: Optional[Program] = None, function: str = ""):
        """Runs [command] at the start of the next tick on the runner thread. [program] and [function] name
        the program function it runs (if any), for stuck_function()."""
        self.command_queue.put((command, program, function))

    def _run_command_queue(self):
        while True:
            try:
                command, program, function = self.command_queue.get_nowait()
            except queue.Empty:
                self.tick_started = None
                return
            # Calling a function that doesn't yield runs all of it here, so it can get stuck here too.
            self.tick_started = time.perf_counter()
            self.tick_program_name = program.name if program is not None else ""
            self.tick_function = function
            command()

    def _drop_removed_programs(self):
        programs = set(self.session.chip.programs)
        for old_program in [p for p in list(self.compiled_program_map) if p not in programs]:
            compiled = self.compiled_program_map.pop(old_program, None)
            if compiled is not None:
                compiled.stop_all()

    def tick(self, current_time: Optional[float] = None):
        """Runs posted commands, advances every running program function by one step and sends the
        solenoid states to the rig."""
        self._run_command_queue()
        current_time = time.perf_counter() if current_time is None else current_time
        self._drop_removed_programs()
        for compiled_program in list(self.compiled_program_map.values()):
            def on_function_start(symbol, program=compiled_program.program):
                self.tick_started = time.perf_counter()
                self.tick_program_name = program.name
                self.tick_function = symbol

            compiled_program.tick(current_time, on_function_start)
        self.tick_started = None
        self.session.rig.flush()

    def tick_reporting_errors(self):
        """tick(), printing an exception instead of raising it, for a loop that keeps ticking."""
        try:
            self.tick()
        except Exception:
            # Print each distinct error once rather than every tick.
            error = traceback.format_exc()
            if error != self.last_error:
                print(error)
            self.last_error = error
        self.tick_started = None

    def stuck_function(self, timeout: float) -> Optional[Tuple[str, str]]:
        """(program name, function name) if one function tick has been running longer than [timeout].

        Each stuck function is reported again only after another [timeout].
        """
        started = self.tick_started
        if started is None or time.perf_counter() - started < timeout:
            return None
        self.tick_started = time.perf_counter()
        return self.tick_program_name, self.tick_function
