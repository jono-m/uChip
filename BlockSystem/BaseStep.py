from BlockSystem.BaseConnectableBlock import BaseConnectableBlock
import typing


class BaseStep(BaseConnectableBlock):
    def __init__(self):
        super().__init__()
        self._isRunning = False
        self._hasRun = False
        self._progress = 0.0

    def SetProgress(self, progress):
        self._progress = max(0.0, min(1.0, progress))

    def GetProgress(self):
        if self._isRunning:
            return self._progress
        else:
            if self._hasRun:
                return 1.0
            else:
                return 0.0

    def IsCompleted(self):
        return self.GetProgress() >= 1.0

    def IsRunning(self):
        return self._isRunning

    def HasRun(self):
        return self._hasRun

    def Start(self):
        if not self.IsValid():
            return
        self._isRunning = True
        self._hasRun = True
        self.OnStepBegan()

    def Stop(self):
        if self._isRunning:
            self.OnStepCompleted()
            self._isRunning = False

    def Reset(self):
        self.Stop()
        self._hasRun = False

    # Overrides
    def OnStepBegan(self):
        pass

    def OnStepTick(self):
        self.SetProgress(1.0)

    def OnStepCompleted(self):
        pass

    def GetNextPorts(self) -> typing.List['BaseStep.CompletedPort']:
        return self.GetPorts(BaseStep.CompletedPort)

    def AddBeginPort(self, label=""):
        return self.AddPort(BaseStep.BeginPort(label))

    def AddCompletedPort(self, label=""):
        return self.AddPort(BaseStep.CompletedPort(label))

    def Update(self):
        super().Update()

        if self._isRunning:
            self.OnStepTick()
            if self.IsCompleted():
                self.Stop()
                [beginPort.GetOwnerBlock().Start() for beginPort in
                 [completedPort.GetConnectedPorts() for completedPort in self.GetNextPorts()]]

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
