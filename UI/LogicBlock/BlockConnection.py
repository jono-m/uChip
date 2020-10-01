from UI.LogicBlock.LogicBlockItem import *


class BlockConnection(ConnectionItem):
    def __init__(self, s: QGraphicsScene, outputWidget: OutputWidget, inputWidget: InputWidget):
        super().__init__(s, outputWidget.portHole, inputWidget.portHole)

        self.inputWidget = inputWidget
        self.outputWidget = outputWidget

        self.inputWidget.inputPort.block.OnConnectionsChanged.Register(self.CheckExistence, True)
        self.outputWidget.outputPort.block.OnConnectionsChanged.Register(self.CheckExistence, True)

    def Remove(self):
        self.SetFromPort(None)
        self.SetToPort(None)
        self.inputWidget.inputPort.block.OnConnectionsChanged.Unregister(self.CheckExistence)
        self.outputWidget.outputPort.block.OnConnectionsChanged.Unregister(self.CheckExistence)
        del self

    def CheckExistence(self):
        if not LogicBlock.IsConnected(self.outputWidget.outputPort, self.inputWidget.inputPort):
            self.Remove()

    def TryDelete(self) -> bool:
        LogicBlock.Disconnect(self.outputWidget.outputPort, self.inputWidget.inputPort)
        return True
