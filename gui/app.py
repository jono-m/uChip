"""Starts the uChip GUI: one session, a runner for its programs ticked on a QThread, and the main window.

The GUI is refreshed from the session on a single timer, so the windows always show the current
state, whether it was changed by the user, by a running program or by the rig.
"""
import os
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from backend.rig import load_rig_from_file
from backend.runner import Runner
from backend.session import new_session
from gui.main_window import build_main_window
from gui.runner_thread import start_runner_thread

# How often Python switches threads (default 5 ms). While the GUI thread runs Python code, the runner
# thread has to wait up to this long for its tick. Measured on Windows, 1 ms gives the steadiest ticks;
# anything shorter causes regular ~20 ms stalls.
THREAD_SWITCH_INTERVAL = 0.001
REFRESH_INTERVAL_MS = 50
STUCK_CHECK_INTERVAL_MS = 1000

DEVICES_FILE = Path("devices.json")


def run(chip_path: Optional[Path] = None) -> int:
    app = QApplication(sys.argv)
    sys.setswitchinterval(THREAD_SWITCH_INTERVAL)

    rig = load_rig_from_file(DEVICES_FILE)
    rig.rescan_devices()
    session = new_session(rig)
    runner = Runner(session)
    runner_thread = start_runner_thread(runner)

    main = build_main_window(session, runner, on_devices_changed=lambda: rig.save_devices(DEVICES_FILE))
    main.window.show()
    if chip_path is not None:
        main.open_chip(chip_path)

    refresh_timer = QTimer()
    refresh_timer.timeout.connect(main.refresh)
    refresh_timer.start(REFRESH_INTERVAL_MS)
    stuck_timer = QTimer()
    stuck_timer.timeout.connect(main.check_stuck)
    stuck_timer.start(STUCK_CHECK_INTERVAL_MS)
    main.refresh()

    result = app.exec()
    stopped = runner_thread.stop()
    rig.disconnect_all()
    rig.save_devices(DEVICES_FILE)
    if not stopped:
        # A program function is stuck on the runner thread, and a thread can't be stopped from outside. Python
        # can't shut down cleanly while it runs (the process would crash on exit), so leave directly.
        print("A program function is still blocking the runner thread; exiting without waiting for it.",
              file=sys.stderr)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(result)
    return result
