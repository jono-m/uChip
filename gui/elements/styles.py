"""Colors and styles shared by the element modules.

Widgets use the system theme. The only custom colors are states: valves open/closed, and running or
paused program functions.
"""
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

# State colors, the same in light and dark themes: (fill, border/pressed, hover).
GREEN = ("#2e8b57", "#1f5f3b", "#36a165")
RED = ("#b3383c", "#7d2729", "#c74448")
AMBER = ("#c98a1b", "#8f6213", "#dd9a23")

# A button filled with a state color. Formatted with one of the colors above.
STATE_BUTTON_STYLE = """
QPushButton {{ background-color: {0}; color: white; border: 1px solid {1}; border-radius: 4px; font-weight: bold;
              padding: 3px 8px; }}
QPushButton:hover {{ background-color: {2}; }}
QPushButton:pressed {{ background-color: {1}; }}
"""


def is_dark_theme() -> bool:
    return QApplication.palette().color(QPalette.Window).lightness() < 128
