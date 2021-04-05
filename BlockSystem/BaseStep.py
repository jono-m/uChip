from BlockSystem.BaseLogicBlock import BaseLogicBlock, Port
import typing


class BaseStep(BaseLogicBlock):
    def __init__(self):
        super().__init__()
        self.isRunning = False
        self.hasRun = False
        self.progress = 0.0

    def GetBeginPorts(self):
        return [port for port in self.GetPorts() if isinstance(port, BeginPort)]

    def GetCompletedPorts(self):
        return [port for port in self.GetPorts() if isinstance(port, CompletedPort)]

    def CreateBeginPort(self, name: str = "Begin"):
        newPort = BeginPort(name)
        self.AddPort(newPort)
        return newPort

    def CreateCompletedPort(self, name: str = "Completed"):
        newPort = CompletedPort(name)
        self.AddPort(newPort)
        return newPort

    def GetProgress(self):
        if self.isRunning:
            return max(0.0, min(1.0, self.progress))
        else:
            if self.hasRun:
                return 1.0
            else:
                return 0.0

    def OnProcedureBegan(self):
        self.hasRun = False

    def OnStepBegan(self):
        self.isRunning = True

    def OnStepCompleted(self):
        self.hasRun = True
        self.isRunning = False

    def GetNextPorts(self) -> typing.List['CompletedPort']:
        return sum([completedPort.GetConnectedPorts() for completedPort in self.GetCompletedPorts()], [])

    def OnProcedureStopped(self):
        self.isRunning = False

    def Update(self):
        super().Update()
        if self.isRunning:
            self.UpdateRunning()
            if self.progress >= 1.0:
                self.OnStepCompleted()

    def UpdateRunning(self):
        self.progress = 1.0

    def GetName(self):
        return "Unnamed Step"


class BeginPort(Port):
    def __init__(self, name="Begin"):
        super().__init__(name)

    def CanConnect(self, port: 'Port'):
        return super().CanConnect(port) and isinstance(port, CompletedPort)


class CompletedPort(Port):
    def __init__(self, name="Completed"):
        super().__init__(name)

    def CanConnect(self, port: 'Port'):
        return super().CanConnect(port) and isinstance(port, BeginPort)
