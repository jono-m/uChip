import typing as _typing


class Parameter:
    def __init__(self, parameterType, defaultValue=None):
        self.type = parameterType
        self.defaultValue = defaultValue

    def Set(self, value):
        pass

    def Get(self) -> _typing.Any:
        pass


class Trigger(Parameter):
    def __init__(self, label, onTriggered: _typing.Callable[[], _typing.Any]):
        super().__init__(self, None)
        self.onTriggered = onTriggered
        self.label = label


class Valve:
    def SetOpen(self, state: bool):
        pass

    def IsOpen(self) -> bool:
        pass


class Program:
    def Start(self):
        pass

    def IsRunning(self) -> bool:
        return False

    def Pause(self):
        pass

    def Stop(self):
        pass

    def Resume(self):
        pass

    def FindParameter(self, displayName: str) -> Parameter:
        pass


class Stop:
    pass


class WaitForSeconds:
    def __init__(self, seconds: float):
        self.seconds = seconds


def WaitForMinutes(minutes: float):
    return WaitForSeconds(60 * minutes)


def WaitForHours(hours: float):
    return WaitForMinutes(60 * hours)


def FindValve(name: str) -> Valve:
    pass


def FindProgram(name: str) -> Program:
    pass


def SetDescription(description: str):
    pass
