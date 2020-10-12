from UI.Procedure.StepBlockItem import *
from Procedures.BasicSteps import *
from UI.WorldBrowser.PortHoles import *


class BeginPortHole(PortHoleWidget):
    def __init__(self, port: BeginPort,
                 graphicsParent: QGraphicsProxyWidget):
        super().__init__(graphicsParent)
        self.beginPort = port
        self.connectionClass = StepConnection

    def CanConnect(self, other: "PortHoleWidget") -> bool:
        if other is None or not isinstance(other, CompletedPortHole):
            return False
        else:
            return Step.CanConnectSteps(other.completedPort, self.beginPort)

    def DoConnect(self, other: "PortHoleWidget"):
        if isinstance(other, CompletedPortHole):
            Step.ConnectToStep(other.completedPort, self.beginPort)


class CompletedPortHole(PortHoleWidget):
    def __init__(self, port: CompletedPort,
                 graphicsParent: QGraphicsProxyWidget):
        super().__init__(graphicsParent)
        self.completedPort = port
        self.connectionClass = StepConnection

    def CanConnect(self, other: "PortHoleWidget") -> bool:
        if other is None or not isinstance(other, BeginPortHole):
            return False
        else:
            return Step.CanConnectSteps(self.completedPort, other.beginPort)

    def DoConnect(self, other: "PortHoleWidget"):
        if isinstance(other, BeginPortHole):
            Step.ConnectToStep(self.completedPort, other.beginPort)


class StepConnection(ConnectionItem):
    def __init__(self, s: QGraphicsScene, beginPortHole: BeginPortHole, completedPortHole: CompletedPortHole):
        super().__init__(s, beginPortHole, completedPortHole)

        self.GetToPortHole().beginPort.step.OnConnectionsChanged.Register(self.CheckExistence, True)
        self.GetFromPortHole().completedPort.step.OnConnectionsChanged.Register(self.CheckExistence, True)

    def Destroy(self):
        self.SetPortHoleA(None)
        self.SetPortHoleB(None)
        self.GetFromPortHole().beginPort.step.OnConnectionsChanged.Unregister(self.CheckExistence)
        self.GetToPortHole().completedPort.step.OnConnectionsChanged.Unregister(self.CheckExistence)
        del self

    def CheckExistence(self):
        if not Step.AreStepsConnected(self.completedWidget.completedPortHole, self.beginWidget.beginPortHole):
            self.Destroy()

    def GetFromPortHole(self):
        if isinstance(self._portHoleA, CompletedPortHole):
            return self._portHoleA
        if isinstance(self._portHoleB, CompletedPortHole):
            return self._portHoleB

    def GetToPortHole(self):
        if isinstance(self._portHoleA, BeginPortHole):
            return self._portHoleA
        if isinstance(self._portHoleB, BeginPortHole):
            return self._portHoleB

    def GetPath(self):
        fromCenter = self.GetFromCenter()
        toCenter = self.GetToCenter()

        path = QPainterPath(fromCenter)

        wide = 200
        down = 100

        if fromCenter.y() > toCenter.y():
            # Need a loop connection

            # Down
            path.lineTo(fromCenter + QPointF(0, down))
            if toCenter.x() > fromCenter.x():
                # Right
                path.lineTo(path.currentPosition() + QPointF(wide, 0))
            else:
                # Left
                path.lineTo(path.currentPosition() - QPointF(wide, 0))
            path.lineTo(QPointF(path.currentPosition().x(), toCenter.y() - down))
            path.lineTo(toCenter - QPointF(0, down))
        else:
            # Need an elbow connection
            midY = (fromCenter.y() + toCenter.y()) / 2
            path.lineTo(QPointF(fromCenter.x(), midY))
            path.lineTo(QPointF(toCenter.x(), midY))

        path.lineTo(toCenter)
        return path

    def TryDelete(self) -> bool:
        Step.DisconnectSteps(self.completedWidget.completedPortHole, self.beginWidget.beginPortHole)
        return True
