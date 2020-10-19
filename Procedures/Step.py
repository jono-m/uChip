from LogicBlocks.LogicBlock import *


class Step(LogicBlock):
    def __init__(self):
        super().__init__()
        self._beginPorts: typing.List[BeginPort] = []
        self._completedPorts: typing.List[CompletedPort] = []

        self._running = False
        self._hasRun = False

    def GetBeginPorts(self):
        return self._beginPorts.copy()

    def GetCompletedPorts(self):
        return self._completedPorts.copy()

    def AddBeginPort(self, name: str = "Begin"):
        newPort = BeginPort(self, name)
        self._beginPorts.append(newPort)
        self.OnPortsChanged.Invoke(self)
        return newPort

    def RemoveBeginPort(self, port: 'BeginPort'):
        self._beginPorts.remove(port)
        self.OnPortsChanged.Invoke(self)

    def AddCompletedPort(self, name: str = "Completed"):
        newPort = CompletedPort(self, name)
        self._completedPorts.append(newPort)
        self.OnPortsChanged.Invoke(self)
        return newPort

    def RemoveCompletedPort(self, port: 'CompletedPort'):
        self._completedPorts.remove(port)
        self.OnPortsChanged.Invoke(self)

    def IsRunning(self):
        return self._running

    def GetProgress(self):
        if self._hasRun:
            return 1.0
        else:
            return 0.0

    @staticmethod
    def ConnectToStep(completedPort: 'CompletedPort', beginPort: 'BeginPort'):
        if beginPort is not None and completedPort is not None:
            beginPort.connectedCompleted.append(completedPort)
            completedPort.connectedBegin.append(beginPort)
            beginPort.step.OnConnectionsChanged.Invoke()
            completedPort.step.OnConnectionsChanged.Invoke()
            completedPort.step.OnRefresh.Invoke((completedPort, beginPort))

    @staticmethod
    def DisconnectSteps(completedPort: 'CompletedPort', beginPort: 'BeginPort'):
        if not Step.AreStepsConnected(completedPort, beginPort):
            return
        if beginPort is not None and completedPort is not None:
            beginPort.connectedCompleted.remove(completedPort)
            completedPort.connectedBegin.remove(beginPort)
            beginPort.block.OnConnectionsChanged.Invoke()
            completedPort.block.OnConnectionsChanged.Invoke()


    @staticmethod
    def AreStepsConnected(completedPort: 'CompletedPort', beginPort: 'BeginPort'):
        if beginPort not in beginPort.step.GetBeginPorts() or completedPort not in completedPort.step.GetCompletedPorts():
            return False
        if beginPort not in completedPort.connectedBegin or completedPort not in beginPort.connectedCompleted:
            return False
        return True

    @staticmethod
    def CanConnectSteps(completedPort: 'CompletedPort', beginPort: 'BeginPort'):
        if beginPort is None or completedPort is None:
            return False

        if beginPort.step == completedPort.step:
            return False

        if beginPort in completedPort.connectedBegin or completedPort in beginPort.connectedCompleted:
            return False

        return True

    def DisconnectAll(self):
        super().DisconnectAll()
        for beginPort in self.GetBeginPorts():
            for completedPort in beginPort.connectedCompleted[:]:
                self.DisconnectSteps(completedPort, beginPort)
        for completedPort in self.GetCompletedPorts():
            for beginPort in completedPort.connectedBegin[:]:
                self.DisconnectSteps(completedPort, beginPort)

    def BeginProcedure(self):
        self._hasRun = False

    def BeginStep(self):
        self._running = True

    # Returns true when the step is completed
    def UpdateStep(self) -> bool:
        return True

    def FinishStep(self):
        self._running = False
        self._hasRun = True

    def StopProcedure(self):
        self._running = False

    # Returns the steps to execute after this step is completed
    def GetNextSteps(self) -> typing.List['Step']:
        if len(self._completedPorts) > 0:
            return self._completedPorts[0].GetSteps()
        else:
            return []

    def GetName(self=None):
        return "Unnamed Step"


class BeginPort(Port):
    def __init__(self, step: Step, name="Begin"):
        super().__init__(step, name)
        self.step = step
        self.connectedCompleted: typing.List[CompletedPort] = []


class CompletedPort(Port):
    def __init__(self, step: Step, name="Completed"):
        super().__init__(step, name)
        self.step = step
        self.connectedBegin: typing.List[BeginPort] = []

    def GetSteps(self) -> typing.List[Step]:
        return [begin.step for begin in self.connectedBegin]
