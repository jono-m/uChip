from UI.LogicBlock.LogicBlockItem import *
from Procedures.BasicSteps import *
from UI.Procedure.StepProgressBar import *


class StepBlockItem(LogicBlockItem):
    def __init__(self, s: QGraphicsScene, step: Step):
        super().__init__(s, step)
        self.step = step

        self.setMinimumWidth(100)

        temp = QWidget()
        temp.setLayout(self.container.layout())

        swapLayout = QHBoxLayout()
        swapLayout.addWidget(temp)

        swapLayout.setSpacing(0)
        swapLayout.setContentsMargins(0, 0, 0, 0)

        self.container.setLayout(swapLayout)

        self.progressWidget = StepProgressBar()
        swapLayout.addWidget(self.progressWidget)

        procedureLayout = QVBoxLayout()
        swapLayout.addLayout(procedureLayout)

        self.beginPortsWidget = QFrame()
        self.beginPortsWidget.setLayout(QHBoxLayout())
        self.beginPortsWidget.layout().setContentsMargins(0, 0, 0, 0)
        self.beginPortsWidget.layout().setSpacing(0)
        self.beginPortsWidget.setProperty("roundedFrame", True)
        self.beginPortsWidget.setStyleSheet("""
        *{
        background-color: rgba(255, 255, 255, 0.05);
        border-width: 0px;
        border-top-left-radius:0px;
        border-bottom-left-radius:0px;
        border-bottom-right-radius:0px;
        }""")
        procedureLayout.addWidget(self.beginPortsWidget)

        self.completedPortsWidget = QFrame()
        self.completedPortsWidget.setLayout(QHBoxLayout())
        self.completedPortsWidget.layout().setContentsMargins(0, 0, 0, 0)
        self.completedPortsWidget.layout().setSpacing(0)
        self.completedPortsWidget.setProperty("roundedFrame", True)
        self.completedPortsWidget.setStyleSheet("""
        *{
        background-color: rgba(255, 255, 255, 0.1);
        border-width: 0px;
        border-top-left-radius:0px;
        border-top-right-radius:0px;
        border-bottom-left-radius:0px;
        }""")
        procedureLayout.addWidget(self.completedPortsWidget)

        self.container.setStyleSheet(self.container.styleSheet() + """
            *[isStart=true] {
                background-color: rgba(20, 100, 20, 0.8);
            }
            *[isActive=true] {
                border: 6px solid rgba(245, 215, 66, 1);
                margin: 0px;
            }
        """)
        self.container.setProperty("isStart", isinstance(self.step, StartStep))

        self.step.OnOutputsUpdated.Register(self.UpdateProgress, True)

        self.UpdatePorts()

        self.UpdateProgress()

        self.setStyle(self.style())

    def Remove(self):
        super().Remove()
        self.step.OnOutputsUpdated.Unregister(self.UpdateProgress)

    def UpdateProgress(self):
        self.progressWidget.SetProgress(self.step.GetProgress())
        self.container.setProperty('isActive', self.step.IsRunning())
        self.setStyle(self.style())

    def UpdatePorts(self):
        super().UpdatePorts()

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

        self.portHole = BeginPortHole(self, graphicsParent)
        self.portHole.Color = QColor(235, 195, 52)

        self.nameLabel = QLabel()

        self.setStyleSheet("*{background-color:transparent;}")
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.portHole, alignment=Qt.AlignCenter)
        layout.addWidget(self.nameLabel, alignment=Qt.AlignCenter)

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
        self.portHole = CompletedPortHole(self, graphicsParent)

        self.portHole.Color = QColor(235, 195, 52)
        self.nameLabel = QLabel()

        self.setStyleSheet("*{background-color:transparent;}")
        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.portHole, alignment=Qt.AlignCenter)
        layout.addWidget(self.nameLabel, alignment=Qt.AlignCenter)

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


class BeginPortHole(PortHoleWidget):
    def __init__(self, portWidget: BeginPortWidget,
                 graphicsParent: QGraphicsProxyWidget):
        super().__init__(graphicsParent)
        self.portWidget = portWidget


class CompletedPortHole(PortHoleWidget):
    def __init__(self, portWidget: CompletedPortWidget,
                 graphicsParent: QGraphicsProxyWidget):
        super().__init__(graphicsParent)
        self.portWidget = portWidget
