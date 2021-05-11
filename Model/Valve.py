from enum import Enum, auto
from PySide6.QtCore import QPointF


class ValveState(Enum):
    OPEN = auto()
    CLOSED = auto()


class Valve:
    def __init__(self):
        self.name = "Valve"
        self.position = QPointF(0, 0)
        self.solenoidNumber = 0
        self.state = ValveState.OPEN
