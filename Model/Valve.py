from enum import Enum, auto
from PySide6.QtCore import QPointF


class ValveState(Enum):
    OPEN = auto()
    CLOSED = auto()


class Valve:
    def __init__(self, name="Valve", position=QPointF(), state=ValveState.OPEN):
        self._name = name
        self._position = position
        self._state = state

    def GetName(self):
        return self._name

    def SetName(self, name: str):
        self._name = name

    def GetPosition(self):
        return self._position

    def SetPosition(self, position: QPointF):
        self._position = position

    def GetState(self):
        return self._state

    def SetState(self, state: 'ValveState'):
        self._state = state
