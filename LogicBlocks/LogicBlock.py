from Util import *
from PySide2.QtCore import *


class LogicBlock:
    def __init__(self):
        self._inputs: typing.List[InputPort] = []
        self._outputs: typing.List[OutputPort] = []

        self.OnOutputsUpdated = Event()  # Called when the logic block computes new outputs
        self.OnConnectionsChanged = Event()  # Called when the logic block gains or loses a connection
        self.OnOutputConnected = Event()  # Called when an output of this block becomes connected
        self.OnPortsChanged = Event()  # Called when an input or output port is added or removed from the logic block
        self.OnDefaultChanged = Event()  # Called when a default value is changed
        self.OnDestroyed = Event()  # Called when this block is destroyed
        self.OnClosed = Event()
        self.OnDuplicated = Event()
        self.OnMoved = Event()

        self.timer = QTimer()
        self.timer.timeout.connect(self.Timeout)
        self.timer.start(33)

        self._position = QPointF(0, 0)

        self.isDestroyed = False

    def Timeout(self):
        self.OnOutputsUpdated.Invoke()

    def __getstate__(self):
        state = self.__dict__.copy()
        state['timer'] = None
        return state

    def __setstate__(self, state):
        state['timer'] = QTimer()
        self.__dict__.update(state)
        self.timer.timeout.connect(self.Timeout)
        self.timer.start(100)

    def GetPosition(self):
        return self._position

    def SetPosition(self, position: QPointF):
        self._position = position
        self.OnMoved.Invoke(self)

    def GetInputs(self):
        return self._inputs.copy()

    def GetOutputs(self):
        return self._outputs.copy()

    def Destroy(self):
        if not self.isDestroyed:
            self.timer.stop()
            self.isDestroyed = True
            self.DisconnectAll()
            self.OnDestroyed.Invoke(self)

    def Close(self):
        self.timer.stop()
        self.OnClosed.Invoke(self)

    def AddInput(self, name: str, dataType: typing.Optional[typing.Type], isConnectable=True) -> 'InputPort':
        newPort = InputPort(self, name, dataType, isConnectable)
        self._inputs.append(newPort)
        self.OnPortsChanged.Invoke(self)
        return newPort

    def RemoveInput(self, inputPort: 'InputPort'):
        self._inputs.remove(inputPort)
        LogicBlock.Disconnect(inputPort.connectedOutput, inputPort)
        self.OnPortsChanged.Invoke(self)

    def AddOutput(self, name: str, dataType: typing.Optional[typing.Type]) -> 'OutputPort':
        newPort = OutputPort(self, name, dataType)
        self._outputs.append(newPort)
        self.OnPortsChanged.Invoke(self)
        return newPort

    def RemoveOutput(self, outputPort: 'OutputPort'):
        self._outputs.remove(outputPort)
        for inputPort in outputPort.connectedInputs:
            LogicBlock.Disconnect(outputPort, inputPort)
        self.OnPortsChanged.Invoke(self)

    def Duplicate(self) -> 'LogicBlock':
        newBlock = type(self)()
        for i in range(len(self._inputs)):
            newBlock._inputs[i].SetDefaultData(self._inputs[i].GetDefaultData())
        newBlock.SetPosition(self.GetPosition())
        self.OnDuplicated.Invoke(newBlock)
        return newBlock

    def UpdateOutputs(self):
        pass

    @staticmethod
    def Connect(outputPort: 'OutputPort', inputPort: 'InputPort'):
        if inputPort is not None and outputPort is not None:
            if inputPort.connectedOutput is not None:
                LogicBlock.Disconnect(inputPort.connectedOutput, inputPort)
            outputPort.connectedInputs.append(inputPort)
            inputPort.connectedOutput = outputPort
            outputPort.block.OnConnectionsChanged.Invoke()
            inputPort.block.OnConnectionsChanged.Invoke()
            outputPort.block.OnOutputConnected.Invoke((outputPort, inputPort))

    @staticmethod
    def Disconnect(outputPort: 'OutputPort', inputPort: 'InputPort', suppressMessages = False):
        if inputPort is not None and outputPort is not None:
            outputPort.connectedInputs.remove(inputPort)
            inputPort.connectedOutput = None
            if not suppressMessages:
                outputPort.block.OnConnectionsChanged.Invoke()
                inputPort.block.OnConnectionsChanged.Invoke()

    @staticmethod
    def IsConnected(outputPort: 'OutputPort', inputPort: 'InputPort'):
        if outputPort not in outputPort.block.GetOutputs() or inputPort not in inputPort.block.GetInputs():
            return False
        if inputPort not in outputPort.connectedInputs:
            return False
        if inputPort.connectedOutput != outputPort:
            return False
        return True

    def DisconnectAll(self, suppressMessages = False):
        changed = []
        for inputPort in self._inputs:
            connectedOutput = inputPort.connectedOutput
            if connectedOutput is not None:
                self.Disconnect(connectedOutput, inputPort, True)
                if inputPort.block not in changed:
                    changed.append(inputPort.block)
                if connectedOutput.block not in changed:
                    changed.append(connectedOutput.block)
        for outputPort in self._outputs:
            for connectedInput in outputPort.connectedInputs[:]:
                self.Disconnect(outputPort, connectedInput, True)
                if outputPort.block not in changed:
                    changed.append(outputPort.block)
                if connectedInput.block not in changed:
                    changed.append(connectedInput.block)

        if not suppressMessages:
            for block in changed:
                block.OnConnectionsChanged.Invoke()

        return changed

    @staticmethod
    def GetName(self=None) -> str:
        return "Unnamed Block"

    # The parent blocks are those connected to the input ports
    def GetParentBlocks(self) -> typing.Set['LogicBlock']:
        parentBlocks = set()
        for inputPort in self._inputs:
            if inputPort.connectedOutput is not None:
                parentBlocks.add(inputPort.connectedOutput.block)
        return parentBlocks

    def GetAllParents(self) -> typing.Set['LogicBlock']:
        expanded: typing.Set[LogicBlock] = set()
        unexpanded: typing.List[LogicBlock] = [self]

        while len(unexpanded) > 0:
            block = unexpanded.pop(0)
            expanded.add(block)
            unexpanded += [x for x in block.GetParentBlocks() if x not in expanded]

        return expanded

    @staticmethod
    def CanConnect(outputPort: 'OutputPort', inputPort: 'InputPort') -> bool:
        if outputPort is None or inputPort is None:
            return False

        if not inputPort.isConnectable:
            return False

        # Don't allow loops (where the output is connected to a parent of the output block, including itself).
        parentsOfOutput = outputPort.block.GetAllParents()
        if inputPort.block in parentsOfOutput:
            return False

        return True


# One input port can connect to one output port. Or, it can be disconnected, in which case a default value
# is used.
class InputPort:
    def __init__(self, block: LogicBlock, name: str, dataType: typing.Type, isConnectable=True):
        self.name: str = name
        self.block: LogicBlock = block
        self.dataType = dataType
        if self.dataType is None:
            self._defaultData = 0
        else:
            self._defaultData = dataType()
        self.connectedOutput: typing.Optional[OutputPort] = None
        self.isConnectable = isConnectable

    def SetDefaultData(self, newValue):
        if self.dataType is None:
            self._defaultData = newValue
        else:
            self._defaultData = self.dataType(newValue)
        self.block.OnDefaultChanged.Invoke(self)

    def GetDefaultData(self):
        return self._defaultData

    def GetData(self):
        if self.connectedOutput is not None:
            if self.dataType is None:
                return self.connectedOutput.GetData()
            else:
                return self.dataType(self.connectedOutput.GetData())
        else:
            return self._defaultData


# One output port can connect to many input ports.
class OutputPort:
    def __init__(self, block: LogicBlock, name: str, dataType: typing.Type):
        self.block: LogicBlock = block
        self.name: str = name
        if dataType is None:
            self._outputData = None
        else:
            self._outputData = dataType()
        self.dataType = dataType
        self.connectedInputs: typing.List[InputPort] = []

    def GetData(self):
        return self._outputData

    def SetData(self, value):
        if self.dataType is None:
            self._outputData = value
        else:
            self._outputData = self.dataType(value)
