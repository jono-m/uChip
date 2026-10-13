"""Starts the uChip GUI: one session, a background runner for its programs, and the main window.

The GUI is refreshed from the session on a single timer, so the windows always show the current
state, whether it was changed by the user, by a running program or by the rig.
"""
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from backend.rig import load_rig_from_file
from backend.runner import Runner
from backend.session import new_session
from gui.main_window import build_main_window

REFRESH_INTERVAL_MS = 50
STUCK_CHECK_INTERVAL_MS = 1000


def run(chip_path: Optional[Path] = None) -> int:
    app = QApplication(sys.argv)

    rig = load_rig_from_file()
    rig.rescan_devices()
    session = new_session(rig)
    runner = Runner(session)
    runner.start()

    main = build_main_window(session, runner, on_devices_changed=lambda: rig.save_devices())
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
    runner.stop()
    rig.disconnect_all()
    rig.save_devices()
    return result
