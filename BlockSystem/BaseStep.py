from BlockSystem.BaseConnectableBlock import BaseConnectableBlock
import typing


class BaseStep(BaseConnectableBlock):
    def __init__(self):
        super().__init__()
        self.isRunning = False
        self.hasRun = False
        self._progress = 0.0

    def GetProgress(self):
        if self.isRunning:
            return self._progress
        else:
            if self.hasRun:
                return 1.0
            else:
                return 0.0

    def IsCompleted(self):
        return self.GetProgress() >= 1.0

    def SetProgress(self, progress):
        self._progress = max(0.0, min(1.0, progress))

    def OnProcedureBegan(self):
        self.hasRun = False

    def OnStepBegan(self):
        self.isRunning = True

    def OnStepTick(self):
        self.SetProgress(1.0)

    def OnStepCompleted(self):
        self.hasRun = True
        self.isRunning = False

    def AddBeginPort(self, label=""):
        return self.AddPort(BaseStep.BeginPort(label))

    def AddCompletedPort(self, label=""):
        return self.AddPort(BaseStep.CompletedPort(label))

    def GetNextPorts(self) -> typing.List['BaseStep.BeginPort']:
        return sum([completedPort.GetConnectedPorts() for completedPort in self.GetPorts(BaseStep.CompletedPort)], [])

    def OnProcedureStopped(self):
        self.isRunning = False

    def Update(self):
        super().Update()

        if self.isRunning:
            self.OnStepTick()
            if self.IsCompleted():
                self.OnStepCompleted()
                for beginPort in self.GetNextPorts():
                    beginPort.GetOwnerBlock().OnStepBegan()

    def GetName(self):
        return "Unnamed Step"

    class BeginPort(BaseConnectableBlock.Port):
        def __init__(self, label=""):
            super().__init__()
            self.label = label

        def CanConnect(self, port: BaseConnectableBlock.Port):
            return super().CanConnect(port) and isinstance(port, BaseStep.CompletedPort)

    class CompletedPort(BaseConnectableBlock.Port):
        def __init__(self, label=""):
            super().__init__()
            self.label = label

        def CanConnect(self, port: BaseConnectableBlock.Port):
            return super().CanConnect(port) and isinstance(port, BaseStep.BeginPort)
