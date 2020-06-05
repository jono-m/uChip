from LogicBlocks.LogicBlock import *


class IfLogicBlock(LogicBlock):
    def __init__(self):
        super().__init__()
        self.output = self.AddOutput("Out", None)
        self.conditionInput = self.AddInput("Condition", bool)
        self.trueInput = self.AddInput("If YES", None)
        self.falseInput = self.AddInput("If NO", None)

    def UpdateOutputs(self):
        if self.conditionInput.GetData():
            self.output.SetData(self.trueInput.GetData())
        else:
            self.output.SetData(self.falseInput.GetData())
        super().UpdateOutputs()

    def GetName(self=None):
        return "If/Else (Branch)"


class ComparisonLogicBlock(LogicBlock):
    def __init__(self, operation):
        super().__init__()
        self.output = self.AddOutput("Out", bool)
        self.inputA = self.AddInput("A", float)
        self.inputB = self.AddInput("B", float)
        self.operation = operation

    def UpdateOutputs(self):
        self.output.SetData(self.operation(self.inputA.GetData(), self.inputB.GetData()))
        super().UpdateOutputs()


class EqualsBlock(ComparisonLogicBlock):
    def __init__(self):
        super().__init__(lambda a, b: a == b)

    def GetName(self=None):
        return "A equals (==) B"


class NEqualsBlock(ComparisonLogicBlock):
    def __init__(self):
        super().__init__(lambda a, b: a != b)

    def GetName(self=None):
        return "A does not equal (!=) B"


class LThanBlock(ComparisonLogicBlock):

    def __init__(self):
        super().__init__(lambda a, b: a < b)

    def GetName(self=None):
        return "A less than (<) B"


class GThanBlock(ComparisonLogicBlock):
    def __init__(self):
        super().__init__(lambda a, b: a > b)

    def GetName(self=None):
        return "A greater than (>) B"


class LThanEBlock(ComparisonLogicBlock):

    def __init__(self):
        super().__init__(lambda a, b: a <= b)

    def GetName(self=None):
        return "A less than or equal to (<=) B"


class GThanEBlock(ComparisonLogicBlock):
    def __init__(self):
        super().__init__(lambda a, b: a >= b)

    def GetName(self=None):
        return "A greater than or equal to (>=) B"
