from enum import Enum, auto
from PySide6.QtCore import QPointF


class ValveState(Enum):
    OPEN = auto()
    CLOSED = auto()

    def Inverted(self):
        return {ValveState.OPEN: ValveState.CLOSED,
                ValveState.CLOSED: ValveState.OPEN}[self]


class Valve:
    def __init__(self):
        self.name = "Valve"
        self.position = QPointF()
        self.solenoidNumber = 0
        self.state = ValveState.OPEN

    def Toggle(self):
        self.state = self.state.Inverted()
