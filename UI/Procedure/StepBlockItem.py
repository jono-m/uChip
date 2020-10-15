from UI.Procedure.StepConnection import *
from UI.LogicBlock.LogicBlockItem import *
from UI.Procedure.StepProgressBar import *


class StepBlockItem(LogicBlockItem):
    def __init__(self, s: QGraphicsScene, step: Step):
        self.step = step

        procedureLayout = QVBoxLayout()
        procedureLayout.setContentsMargins(0, 0, 0, 0)
        procedureLayout.setSpacing(0)
        self.beginPortsWidget = QFrame()
        self.beginPortsWidget.setLayout(QHBoxLayout())
        self.beginPortsWidget.setProperty("roundedFrame", True)
        procedureLayout.addWidget(self.beginPortsWidget)

        self.completedPortsWidget = QFrame()
        self.completedPortsWidget.setLayout(QHBoxLayout())
        self.completedPortsWidget.setProperty("roundedFrame", True)
        procedureLayout.addWidget(self.completedPortsWidget)

        super().__init__(s, step)

        temp = QWidget()
        temp.setLayout(self.container.layout())

        swapLayout = QHBoxLayout()
        swapLayout.setContentsMargins(0, 0, 0, 0)
        swapLayout.setSpacing(0)
        swapLayout.addWidget(temp)

        self.container.setLayout(swapLayout)

        self.progressWidget = StepProgressBar()
        swapLayout.addWidget(self.progressWidget)

        swapLayout.addLayout(procedureLayout)

        self.container.setProperty("isStart", isinstance(self.step, StartStep))

        self.step.OnOutputsUpdated.Register(self.UpdateProgress, True)

        self.UpdatePorts()
        self.UpdateProgress()

    def Destroy(self):
        super().Destroy()
        self.step.OnOutputsUpdated.Unregister(self.UpdateProgress)

    def UpdateProgress(self):
        self.progressWidget.SetProgress(self.step.GetProgress())
        self.container.setProperty('isActive', self.step.IsRunning())
        self.setStyle(self.style())

    def UpdatePorts(self):
        super().UpdatePorts()

        if self.beginPortsWidget is None:
            return

        beginPorts = [beginWidget.beginPort for beginWidget in self.beginPortsWidget.children() if
                      isinstance(beginWidget, BeginPortWidget)]
        for beginPort in self.step.GetBeginPorts():
            if beginPort not in beginPorts:
                beginWidget = BeginPortWidget(beginPort, self)
                self.beginPortsWidget.layout().addWidget(beginWidget)

        completedPorts = [completedWidget.completedPort for completedWidget in self.completedPortsWidget.children() if
                          isinstance(completedWidget, CompletedPortWidget)]
        for completedPort in self.step.GetCompletedPorts():
            if completedPort not in completedPorts:
                completedWidget = CompletedPortWidget(completedPort, self)
                self.completedPortsWidget.layout().addWidget(completedWidget)

    def DoMove(self, currentPosition: QPointF, delta: QPointF):
        super().DoMove(currentPosition, delta)

        completedPorts = [x for x in self.completedPortsWidget.children() if isinstance(x, CompletedPortWidget)]
        for completedPort in completedPorts:
            completedPort.Update()

    def TryDelete(self):
        if isinstance(self.step, StartStep):
            return False
        return super().TryDelete()

    def TryDuplicate(self) -> typing.Optional['SelectableItem']:
        if isinstance(self.step, StartStep):
            return None
        else:
            return super().TryDuplicate()


class BeginPortWidget(QFrame):
    def __init__(self, port: BeginPort, graphicsParent: QGraphicsProxyWidget):
        super().__init__()

        self.beginPort = port

        self.portHole = BeginPortHole(port, graphicsParent)
        self.portHole.Color = QColor(235, 195, 52)

        self.nameLabel = QLabel()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        layout.addWidget(self.portHole)
        layout.addWidget(self.nameLabel)

        self.beginPort.step.OnConnectionsChanged.Register(self.Update, True)
        self.beginPort.step.OnPortsChanged.Register(self.Update, True)
        self.beginPort.step.OnDestroyed.Register(self.Remove, True)

        self.Update()

    def Remove(self):
        self.beginPort.step.OnConnectionsChanged.Unregister(self.Update)
        self.beginPort.step.OnPortsChanged.Unregister(self.Update)
        self.beginPort.step.OnDestroyed.Unregister(self.Remove)
        self.deleteLater()

    def Update(self):
        if self.beginPort not in self.beginPort.step.GetBeginPorts():
            self.Remove()
            return

        self.nameLabel.setText(self.beginPort.name)
        self.portHole.SetIsFilled(len(self.beginPort.connectedCompleted) > 0)


class CompletedPortWidget(QFrame):
    def __init__(self, port: CompletedPort, graphicsParent: QGraphicsProxyWidget):
        super().__init__()
        self.completedPort = port
        self.portHole = CompletedPortHole(port, graphicsParent)

        self.portHole.Color = QColor(235, 195, 52)
        self.nameLabel = QLabel()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        layout.addWidget(self.portHole)
        layout.addWidget(self.nameLabel)

        self.completedPort.step.OnConnectionsChanged.Register(self.Update, True)
        self.completedPort.step.OnPortsChanged.Register(self.Update, True)
        self.completedPort.step.OnDestroyed.Register(self.Remove, True)

        self.Update()

    def Remove(self):
        self.completedPort.step.OnConnectionsChanged.Unregister(self.Update)
        self.completedPort.step.OnPortsChanged.Unregister(self.Update)
        self.completedPort.step.OnDestroyed.Unregister(self.Remove)
        self.deleteLater()

    def Update(self):
        if self.completedPort not in self.completedPort.step.GetCompletedPorts():
            self.Remove()
            return

        self.portHole.SetIsFilled(len(self.completedPort.connectedBegin) > 0)

        self.nameLabel.setText(self.completedPort.name)
