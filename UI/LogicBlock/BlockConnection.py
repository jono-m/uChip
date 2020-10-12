from UI.WorldBrowser.PortHoles import *


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

        self.GetToPortHole().inputPort.block.OnConnectionsChanged.Register(self.CheckExistence, True)
        self.GetFromPortHole().outputPort.block.OnConnectionsChanged.Register(self.CheckExistence, True)

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
        self.SetPortHoleA(None)
        self.SetPortHoleB(None)
        self.GetToPortHole().inputPort.block.OnConnectionsChanged.Unregister(self.CheckExistence)
        self.GetFromPortHole().outputPort.block.OnConnectionsChanged.Unregister(self.CheckExistence)
        del self

    def CheckExistence(self):
        if not LogicBlock.IsConnected(self.outputWidget.outputPort, self.inputWidget.inputPort):
            self.Remove()

    def TryDelete(self) -> bool:
        LogicBlock.Disconnect(self.outputWidget.outputPort, self.inputWidget.inputPort)
        return True
