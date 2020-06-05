from LogicBlocks.LogicBlock import *


class BooleanLogicBlock(LogicBlock):
    def __init__(self):
        super().__init__()
        self.input = self.AddInput("Value", bool, False)
        self.output = self.AddOutput("Out", bool)

    def GetName(self=None):
        return "Boolean Constant"

    def UpdateOutputs(self):
        self.output.SetData(self.input.GetData())
        super().UpdateOutputs()


class AndLogicBlock(LogicBlock):
    def __init__(self):
        super().__init__()
        self.output = self.AddOutput("Out", bool)
        self.aInput = self.AddInput("A", bool)
        self.bInput = self.AddInput("B", bool)

    def UpdateOutputs(self):
        self.output.SetData(self.aInput.GetData() and self.bInput.GetData())
        super().UpdateOutputs()

    def GetName(self=None):
        return "And"


class OrLogicBlock(LogicBlock):
    def __init__(self):
        super().__init__()
        self.output = self.AddOutput("Out", bool)
        self.aInput = self.AddInput("A", bool)
        self.bInput = self.AddInput("B", bool)

    def UpdateOutputs(self):
        self.output.SetData(self.aInput.GetData() or self.bInput.GetData())
        super().UpdateOutputs()

    def GetName(self=None):
        return "Or"


class NotLogicBlock(LogicBlock):
    def __init__(self):
        super().__init__()
        self.output = self.AddOutput("Out", bool)
        self.input = self.AddInput("In", bool)

    def UpdateOutputs(self):
        self.output.SetData(not self.input.GetData())
        super().UpdateOutputs()

    def GetName(self=None):
        return "Not"
