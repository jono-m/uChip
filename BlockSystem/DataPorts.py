from BlockSystem.BaseConnectableBlock import BaseConnectableBlock
from BlockSystem.Data import Data
import typing


class DataPort(BaseConnectableBlock.Port):
    def __init__(self, data: Data):
        super().__init__()
        self._data = data

    def GetName(self):
        return self._data.GetName()

    def SetName(self, name: str):
        return self._data.SetName(name)

    def GetValue(self):
        return self._data.GetValue()

    def SetValue(self, value):
        self._data.SetValue(value)

    def GetData(self):
        return self._data


# One input port can connect to one output port. Or, it can be disconnected, in which case a default value
# is used.
# isConnectable: Set this to false if the port is only for default values
class InputPort(DataPort):
    def GetConnectedOutput(self) -> typing.Optional['OutputPort']:
        if len(self.GetConnectedPorts()) == 0:
            return None
        else:
            return self.GetConnectedPorts()[0]

    def CanConnect(self, port: 'BaseConnectableBlock.Port'):
        if not super().CanConnect(port):
            return False
        if isinstance(port, OutputPort):
            return not DoesConnectionFormLoop(self, port)
        else:
            return False

    def Connect(self, port: 'BaseConnectableBlock.Port'):
        self.DisconnectAll()
        super().Connect(port)

    def GetValue(self):
        connectedOutput = self.GetConnectedOutput()
        if connectedOutput is not None:
            self.GetData().Cast(self.GetConnectedOutput().GetValue())
        else:
            return super().GetValue()


# One output port can connect to many input ports.
class OutputPort(DataPort):
    def CanConnect(self, port: 'BaseConnectableBlock.Port'):
        if not super().CanConnect(port):
            return False
        if isinstance(port, InputPort):
            return port.CanConnect(self)
        else:
            return False


def DoesConnectionFormLoop(inputPort: InputPort, outputPort: OutputPort):
    visitedBlocks: typing.Set[BaseConnectableBlock] = set()

    blocksToVisit = [outputPort.GetOwnerBlock()]
    while blocksToVisit:
        blockToVisit = blocksToVisit.pop(0)
        visitedBlocks.add(blockToVisit)
        for inputPort in blockToVisit.GetPorts(InputPort):
            if inputPort.GetConnectedOutput() is not None:
                block = inputPort.GetConnectedOutput().GetOwnerBlock()
                if block not in visitedBlocks:
                    blocksToVisit.append(block)

    return inputPort.GetOwnerBlock() not in visitedBlocks
