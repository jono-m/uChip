"""Runs the programs of a session's chip.

The runner holds the compiled form of each program on the chip, including its running functions.
Each tick sends the solenoid states to the rig and advances every running function by one step.
start() ticks about once a millisecond on a background thread; a front end without one (such as a
test) can call tick() itself.

Compiled programs whose program is no longer on the session's chip (because it was removed, or
another chip was opened) are dropped on the next tick, which also stops their running functions.

A function that blocks (e.g. an infinite loop without a yield) stalls the loop; stuck_function()
reports that.
"""
import threading
import time
import traceback
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from backend.chip import Program
from backend.programs import CompiledProgram, compile_program
from backend.session import Session


@dataclass(eq=False)
class Runner:
    session: Session
    compiled: Dict[Program, CompiledProgram] = field(default_factory=dict)
    interval: float = 0.001
    stop_event: threading.Event = field(default_factory=threading.Event)
    thread: Optional[threading.Thread] = None
    # The function currently being ticked, and when its tick started.
    tick_started: Optional[float] = None
    tick_program_name: str = ""
    tick_function: str = ""

    def compiled_program(self, program: Program) -> CompiledProgram:
        """The compiled form of [program], (re)compiling it if its script has changed."""
        compiled = self.compiled.get(program)
        if compiled is None or compiled.is_out_of_date():
            compiled = compile_program(program, self.session.chip, self.session.rig, self.compiled_program)
            self.compiled[program] = compiled
        return compiled

    def compile_all(self):
        for program in self.session.chip.programs:
            self.compiled_program(program)

    def _drop_removed_programs(self):
        programs = set(self.session.chip.programs)
        for program in [p for p in self.compiled if p not in programs]:
            self.compiled.pop(program, None)

    def tick(self, now: Optional[float] = None):
        """Sends solenoid states to the rig and advances every running program function by one step."""
        now = time.time() if now is None else now
        self._drop_removed_programs()
        self.session.rig.flush()
        for compiled in list(self.compiled.values()):
            def on_function_start(symbol, program=compiled.program):
                self.tick_started = time.time()
                self.tick_program_name = program.name
                self.tick_function = symbol

            compiled.tick(now, on_function_start)
        self.tick_started = None

    # The background thread

    def _run(self):
        last_error = None
        while not self.stop_event.is_set():
            try:
                self.tick()
            except Exception:
                # Print each distinct error once rather than every tick.
                error = traceback.format_exc()
                if error != last_error:
                    print(error)
                last_error = error
            self.tick_started = None
            self.stop_event.wait(self.interval)

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, name="uChip runner", daemon=True)
        self.thread.start()

    def stop(self, timeout: float = 1.0):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout)
        self.thread = None

    def stuck_function(self, timeout: float) -> Optional[Tuple[str, str]]:
        """(program name, function name) if one function tick has been running longer than [timeout].

        Each stuck function is reported again only after another [timeout].
        """
        started = self.tick_started
        if started is None or time.time() - started < timeout:
            return None
        self.tick_started = time.time()
        return self.tick_program_name, self.tick_function
