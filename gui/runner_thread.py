"""Ticks a runner on a QThread, for the GUI.

A precise QTimer living in the thread ticks the runner at the runner's interval (1 ms, QTimer's
shortest non-zero interval; 0 would keep a core busy). Precise timers use the OS's high-resolution
timer, so ticks stay about 1 ms apart, where a sleeping Python thread on Windows only wakes about
every 15 ms. The thread runs at time-critical priority so other threads don't delay its ticks.

On Windows 11, a process whose windows are all minimized or hidden is power throttled, and its timers
then only fire every ~15.6 ms, so the process opts out of that.
"""
import ctypes
import sys
from dataclasses import dataclass

from PySide6.QtCore import QThread, QTimer, Qt

from backend.runner import Runner


@dataclass(eq=False)
class RunnerThread:
    thread: QThread
    timer: QTimer
    stopping: bool = False

    def stop(self, timeout_ms: int = 1000) -> bool:
        """Stops ticking and waits for the thread to end. False if it didn't end in time (e.g. a
        program function is stuck in a loop)."""
        self.stopping = True
        return self.thread.wait(timeout_ms)


def start_runner_thread(runner: Runner) -> RunnerThread:
    _disable_power_throttling()
    thread = QThread()
    thread.setObjectName("uChip runner")
    timer = QTimer()
    timer.setTimerType(Qt.PreciseTimer)
    timer.setInterval(max(1, round(runner.interval * 1000)))
    timer.moveToThread(thread)
    runner_thread = RunnerThread(thread, timer)

    # Runs on the thread, since the timer lives there; the timer can only be stopped from there too.
    def tick():
        if runner_thread.stopping:
            timer.stop()
            thread.quit()
            return
        runner.tick_reporting_errors()

    timer.timeout.connect(tick)
    thread.started.connect(timer.start)
    thread.start(QThread.TimeCriticalPriority)
    return runner_thread


class _PowerThrottlingState(ctypes.Structure):
    _fields_ = [("Version", ctypes.c_ulong), ("ControlMask", ctypes.c_ulong), ("StateMask", ctypes.c_ulong)]


_PROCESS_POWER_THROTTLING = 4  # PROCESS_INFORMATION_CLASS ProcessPowerThrottling
_THROTTLE_EXECUTION_SPEED = 0x1
_THROTTLE_IGNORE_TIMER_RESOLUTION = 0x4


def _disable_power_throttling():
    """Keeps this process's timers precise and its threads at full speed while its windows are hidden."""
    if sys.platform != "win32":
        return
    # Controlling both throttles with neither set turns them off.
    state = _PowerThrottlingState(1, _THROTTLE_EXECUTION_SPEED | _THROTTLE_IGNORE_TIMER_RESOLUTION, 0)
    kernel32 = ctypes.WinDLL("kernel32")
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    kernel32.SetProcessInformation.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong]
    kernel32.SetProcessInformation(kernel32.GetCurrentProcess(), _PROCESS_POWER_THROTTLING,
                                   ctypes.byref(state), ctypes.sizeof(state))
