import threading
import time
import typing

from UI.UIMaster import UIMaster
from Data.ProgramCompilation import TickFunction, CompiledProgram


class ProgramWorker:
    def __init__(self, timeout: float):
        self.tickStartTime: typing.Optional[float] = None
        self.tickStartProgram: typing.Optional[CompiledProgram] = None
        self.tickStartFunctionSymbol: str = ""
        self.timeout = timeout
        self.thread = threading.Thread(target=self.Loop, daemon=True)
        self.doStop = False
        self.thread.start()

    def Loop(self):
        while not self.doStop:
            for x in UIMaster.GetCompiledPrograms().copy():
                self.tickStartProgram = x
                for s in x.asyncFunctions.copy():
                    self.tickStartTime = time.time()
                    self.tickStartFunctionSymbol = s
                    TickFunction(x, s)
                    self.tickStartTime = None
                time.sleep(0.01)

    def IsStuck(self):
        if self.tickStartTime is None or self.thread is None:
            return False
        if time.time() - self.tickStartTime >= self.timeout:
            self.tickStartTime = time.time()
            return True
