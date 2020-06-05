from UI.Procedure.StepBlockItem import *


class StepConnection(ConnectionItem):
    def __init__(self, s: QGraphicsScene, beginWidget: BeginPortWidget, completedWidget: CompletedPortWidget):
        super().__init__(s, completedWidget.portHole, beginWidget.portHole)

        self.beginWidget = beginWidget
        self.completedWidget = completedWidget

        self.beginWidget.beginPort.step.OnConnectionsChanged.Register(self.CheckExistence, True)
        self.completedWidget.completedPort.step.OnConnectionsChanged.Register(self.CheckExistence, True)

    def Remove(self):
        self.SetFromPort(None)
        self.SetToPort(None)
        self.beginWidget.beginPort.step.OnConnectionsChanged.Unregister(self.CheckExistence)
        self.completedWidget.completedPort.step.OnConnectionsChanged.Unregister(self.CheckExistence)
        self.scene().removeItem(self)

    def CheckExistence(self):
        if not Step.AreStepsConnected(self.completedWidget.completedPort, self.beginWidget.beginPort):
            self.Remove()

    @staticmethod
    def GetPath(fromCenter: QPointF, toCenter: QPointF):
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
        Step.DisconnectSteps(self.completedWidget.completedPort, self.beginWidget.beginPort)
        return True
