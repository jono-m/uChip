from UI.ProjectEditor.PortHoles import *


class InputPortHole(PortHoleWidget):
    def __init__(self, port: InputPort, graphicsParent: QGraphicsProxyWidget):
        super().__init__(graphicsParent)
        self.inputPort = port
        self.connectionClass = BlockConnection

    def CanConnect(self, other: "PortHoleWidget") -> bool:
        if other is None or not isinstance(other, OutputPortHole):
            return False
        else:
            return LogicBlock.CanConnect(other.outputPort, self.inputPort)

    def DoConnect(self, other: "PortHoleWidget"):
        if isinstance(other, OutputPortHole):
            LogicBlock.Connect(other.outputPort, self.inputPort)


class OutputPortHole(PortHoleWidget):
    def __init__(self, port: OutputPort, graphicsParent: QGraphicsProxyWidget):
        super().__init__(graphicsParent)
        self.outputPort = port
        self.connectionClass = BlockConnection

    def CanConnect(self, other: "PortHoleWidget") -> bool:
        if other is None or not isinstance(other, InputPortHole):
            return False
        else:
            return LogicBlock.CanConnect(self.outputPort, other.inputPort)

    def DoConnect(self, other: "PortHoleWidget"):
        if isinstance(other, InputPortHole):
            LogicBlock.Connect(self.outputPort, other.inputPort)


class BlockConnection(ConnectionItem):
    def __init__(self, s: QGraphicsScene, outputPortHole: OutputPortHole, inputPortHole: InputPortHole):
        super().__init__(s, outputPortHole, inputPortHole)

        self.GetToPortHole().inputPort.ownerBlock.OnConnectionsChanged.Register(self.CheckExistence, True)
        self.GetFromPortHole().outputPort.ownerBlock.OnConnectionsChanged.Register(self.CheckExistence, True)

        self.lastData = outputPortHole.outputPort.GetValue()

    def GetFromPortHole(self):
        if isinstance(self._portHoleA, OutputPortHole):
            return self._portHoleA
        if isinstance(self._portHoleB, OutputPortHole):
            return self._portHoleB

    def GetToPortHole(self):
        if isinstance(self._portHoleA, InputPortHole):
            return self._portHoleA
        if isinstance(self._portHoleB, InputPortHole):
            return self._portHoleB

    def Remove(self):
        self.GetToPortHole().inputPort.ownerBlock.OnConnectionsChanged.Unregister(self.CheckExistence)
        self.GetFromPortHole().outputPort.ownerBlock.OnConnectionsChanged.Unregister(self.CheckExistence)
        self.SetPortHoleA(None)
        self.SetPortHoleB(None)
        self.scene().removeItem(self)

    def CheckExistence(self):
        if not LogicBlock.IsConnected(self.GetFromPortHole().outputPort, self.GetToPortHole().inputPort):
            self.Remove()

    def TryDelete(self) -> bool:
        if self.GetFromPortHole() is not None and self.GetToPortHole() is not None:
            LogicBlock.Disconnect(self.GetFromPortHole().outputPort, self.GetToPortHole().inputPort)
            return True
        return False
