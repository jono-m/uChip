from LogicBlocks.LogicBlock import *


class InputLogicBlock(LogicBlock):
    def __init__(self, dataType, isParameter=False):
        super().__init__()
        self.dataType = dataType
        self.blockInputPort: typing.Optional[InputPort] = None
        self.proxyBlock: typing.Optional[LogicBlock] = None
        self.currentValue: typing.Optional[InputPort] = None

        self.nameInput = self.AddInput("Name", str, False)
        self.output = self.AddOutput("Value", self.dataType)

        initialStr = "New" + self.GetTypeAsStr()
        self.nameInput.SetDefaultData(initialStr)

        self.isParameter = isParameter

    def SetupForProxy(self, proxyBlock: LogicBlock):
        self.blockInputPort = proxyBlock.AddInput(self.nameInput.GetDefaultData(), self.dataType)

        self.currentValue = self.blockInputPort
        self._inputs.insert(0, self.currentValue)

        self.proxyBlock = proxyBlock

        self.OnPortsChanged.Invoke(self)

    def GetTypeAsStr(self):
        return str(self.dataType).split('\'')[1].capitalize()

    def GetName(self=None):
        if self.isParameter:
            return self.nameInput.GetData() + " (" + self.GetTypeAsStr() + " Parameter)"
        else:
            return self.nameInput.GetData() + " (" + self.GetTypeAsStr() + " Input)"

    def UpdateOutputs(self):
        self.output.SetData(self.blockInputPort.GetData())
        if self.blockInputPort.name != self.nameInput.GetData():
            self.blockInputPort.name = self.nameInput.GetData()
            self.blockInputPort.block.OnPortsChanged.Invoke(self.blockInputPort.block)
        super().UpdateOutputs()

    def Duplicate(self) -> 'LogicBlock':
        newB = InputLogicBlock(self.dataType, self.isParameter)
        newB.SetupForProxy(self.proxyBlock)
        self.OnDuplicated.Invoke(newB)
        return newB

    def DisconnectAll(self):
        super().DisconnectAll()
        self.proxyBlock.RemoveInput(self.blockInputPort)


class OutputLogicBlock(LogicBlock):
    def __init__(self, dataType):
        super().__init__()
        self.dataType = dataType
        initialStr = "New" + self.GetTypeAsStr()

        self.nameInput = self.AddInput("Name", str, False)
        self.nameInput.SetDefaultData(initialStr)

        self.proxyBlock: typing.Optional[LogicBlock] = None
        self.blockOutputPort: typing.Optional[OutputPort] = None

        self.input = self.AddInput("Value", dataType)

    def SetupForProxy(self, proxyBlock: LogicBlock):
        self.blockOutputPort = proxyBlock.AddOutput(self.nameInput.GetDefaultData(), self.dataType)

        self.proxyBlock = proxyBlock

    def GetTypeAsStr(self):
        return str(self.dataType).split('\'')[1].capitalize()

    def Duplicate(self) -> 'LogicBlock':
        newB = OutputLogicBlock(self.dataType)
        newB.SetupForProxy(self.proxyBlock)
        self.OnDuplicated.Invoke(newB)
        return newB

    def GetName(self=None):
        return "Output: " + self.GetTypeAsStr()

    def UpdateOutputs(self):
        self.blockOutputPort.SetData(self.input.GetData())
        if self.blockOutputPort.name != self.nameInput.GetDefaultData():
            self.blockOutputPort.name = self.nameInput.GetDefaultData()
            self.OnPortsChanged.Invoke()
        super().UpdateOutputs()

    def DisconnectAll(self):
        super().DisconnectAll()
        self.proxyBlock.RemoveOutput(self.blockOutputPort)
