from BlockSystem.BaseConnectableBlock import BaseConnectableBlock, Port
import typing


class BaseLogicBlock(BaseConnectableBlock):
    def __init__(self):
        super().__init__()

    def CreateInputPort(self, name: str, dataType: typing.Union[typing.Type, typing.List, None], defaultValue=None):
        newPort = InputPort(name, dataType, defaultValue)
        self.AddPort(newPort)
        return newPort

    def CreateOutputPort(self, name: str, dataType: typing.Union[typing.Type, typing.List, None]):
        newPort = OutputPort(name, dataType)
        self.AddPort(newPort)
        return newPort

    def GetInputPorts(self):
        return [port for port in self.GetPorts() if isinstance(port, InputPort)]

    def GetOutputPorts(self):
        return [port for port in self.GetPorts() if isinstance(port, OutputPort)]


# One input port can connect to one output port. Or, it can be disconnected, in which case a default value
# is used.
# isConnectable: Set this to false if the port is only for default values
class InputPort(Port):
    def __init__(self, name: str, dataType: typing.Union[typing.Type, typing.List, None], defaultValue=None):
        super().__init__(name)
        self.dataType = dataType
        if type(dataType) == list or dataType is None:
            self._defaultValue = 0
        else:
            self._defaultValue = dataType()

        if defaultValue is not None:
            self.SetDefaultValue(defaultValue)

    def GetConnectedOutput(self) -> typing.Optional['OutputPort']:
        if len(self.GetConnectedPorts()) == 0:
            return None
        else:
            return self.GetConnectedPorts()[0]

    def CanConnect(self, port: 'Port'):
        if not super().CanConnect(port):
            return False
        if isinstance(port, OutputPort):
            return not DoesConnectionFormLoop(self, port)
        else:
            return False

    def Connect(self, port: 'Port'):
        self.DisconnectAll()
        super().Connect(port)

    def SetDefaultValue(self, newValue):
        if type(self.dataType) == list:
            self._defaultValue = max(0, min(len(self.dataType) - 1, int(newValue)))
        elif self.dataType is None:
            self._defaultValue = newValue
        else:
            # Cast over to this block type
            self._defaultValue = self.dataType(newValue)

    def GetDefaultValue(self):
        return self._defaultValue

    def GetValue(self):
        if self.GetConnectedOutput() is not None:
            if type(self.dataType) == list:
                return max(0, min(len(self.dataType), int(self.GetConnectedOutput().GetValue())))
            elif self.dataType is None:
                return self.GetConnectedOutput().GetValue()
            else:
                # Cast over to this block type
                return self.dataType(self.GetConnectedOutput().GetValue())
        else:
            return self._defaultValue


# One output port can connect to many input ports.
class OutputPort(Port):
    def __init__(self, name: str, dataType: typing.Type):
        super().__init__(name)
        self.dataType = dataType
        self._outputValue = dataType()

    def CanConnect(self, port: 'Port'):
        if not super().CanConnect(port):
            return False
        if isinstance(port, InputPort):
            return port.CanConnect(self)
        else:
            return False

    def GetValue(self):
        return self._outputValue

    def SetValue(self, value):
        # Cast over to output data type
        self._outputValue = self.dataType(value)


def DoesConnectionFormLoop(inputPort: InputPort, outputPort: OutputPort):
    visitedBlocks: typing.Set[BaseConnectableBlock] = set()

    blocksToVisit = [outputPort.ownerBlock]
    while blocksToVisit:
        blockToVisit = blocksToVisit.pop(0)
        visitedBlocks.add(blockToVisit)
        if isinstance(blockToVisit, BaseLogicBlock):
            for inputPort in blockToVisit.GetInputPorts():
                if inputPort.GetConnectedOutput() is not None:
                    block = inputPort.GetConnectedOutput().ownerBlock
                    if block not in visitedBlocks:
                        blocksToVisit.append(block)

    return inputPort.ownerBlock not in visitedBlocks
