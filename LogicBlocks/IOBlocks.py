from LogicBlocks.LogicBlock import *


class InputLogicBlock(LogicBlock):
    def __init__(self, dataType, isParameter=False):
        super().__init__()
        self.dataType = dataType
        self.parentBlockInputPort: typing.Optional[InputPort] = None
        self.parentBlock: typing.Optional[LogicBlock] = None

        self.nameInput = self.AddInput("Name", str, False)
        self.output = self.AddOutput("Value", self.dataType)

        initialStr = "New" + self.GetTypeAsStr()
        self.nameInput.SetDefaultData(initialStr)

        self.isParameter = isParameter

    def SetParentBlock(self, parentBlock: LogicBlock):
        self.parentBlockInputPort = parentBlock.AddInput(self.nameInput.GetDefaultData(), self.dataType)

        self._inputs.insert(0, self.parentBlockInputPort)

        self.parentBlock = parentBlock

        self.OnPortsChanged.Invoke(self)

    def GetTypeAsStr(self):
        return str(self.dataType).split('\'')[1].capitalize()

    def GetName(self=None):
        if self.isParameter:
            return self.nameInput.GetData() + " (" + self.GetTypeAsStr() + " Parameter)"
        else:
            return self.nameInput.GetData() + " (" + self.GetTypeAsStr() + " Input)"

    def UpdateOutputs(self):
        self.output.SetData(self.parentBlockInputPort.GetData())
        if self.parentBlockInputPort.name != self.nameInput.GetData():
            self.parentBlockInputPort.name = self.nameInput.GetData()
            self.parentBlockInputPort.block.OnPortsChanged.Invoke(self.parentBlockInputPort.block)
        super().UpdateOutputs()

    def Duplicate(self) -> 'LogicBlock':
        newB = InputLogicBlock(self.dataType, self.isParameter)
        newB.SetParentBlock(self.parentBlock)
        self.OnDuplicated.Invoke(newB)
        return newB

    def Destroy(self):
        super().Destroy()
        self.parentBlock.RemoveInput(self.parentBlockInputPort)


class OutputLogicBlock(LogicBlock):
    def __init__(self, dataType):
        super().__init__()
        self.dataType = dataType
        initialStr = "New" + self.GetTypeAsStr()

        self.nameInput = self.AddInput("Name", str, False)
        self.nameInput.SetDefaultData(initialStr)

        self.parentBlock: typing.Optional[LogicBlock] = None
        self.parentBlockOutputPort: typing.Optional[OutputPort] = None

        self.input = self.AddInput("Value", dataType)

    def SetParentBlock(self, proxyBlock: LogicBlock):
        self.parentBlockOutputPort = proxyBlock.AddOutput(self.nameInput.GetDefaultData(), self.dataType)

        self.parentBlock = proxyBlock

    def GetTypeAsStr(self):
        return str(self.dataType).split('\'')[1].capitalize()

    def Duplicate(self) -> 'LogicBlock':
        newB = OutputLogicBlock(self.dataType)
        newB.SetParentBlock(self.parentBlock)
        self.OnDuplicated.Invoke(newB)
        return newB

    def GetName(self=None):
        return self.nameInput.GetData() + " (" + self.GetTypeAsStr() + " Output)"

    def UpdateOutputs(self):
        self.parentBlockOutputPort.SetData(self.input.GetData())
        if self.parentBlockOutputPort.name != self.nameInput.GetDefaultData():
            self.parentBlockOutputPort.name = self.nameInput.GetDefaultData()
            self.OnPortsChanged.Invoke()
        super().UpdateOutputs()

    def Destroy(self):
        super().Destroy()
        self.parentBlock.RemoveOutput(self.parentBlockOutputPort)
