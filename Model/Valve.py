from enum import Enum, auto


class Valve:
    def __init__(self):
        self.name: str = "Valve"
        self.xPosition: float = 0
        self.yPosition: float = 0
        self._state = ValveState.OPEN

    def GetState(self):
        return self._state

    def SetState(self, state: 'ValveState'):
        self._state = state


class ValveState(Enum):
    OPEN = auto()
    CLOSED = auto()
