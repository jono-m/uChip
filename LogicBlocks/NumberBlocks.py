import time
from LogicBlocks.LogicBlock import *
import math


class NumberLogicBlock(LogicBlock):
    def __init__(self):
        super().__init__()
        self.input = self.AddInput("Value", float, False)
        self.output = self.AddOutput("Out", float)

    def GetName(self=None):
        return "Number Constant"

    def UpdateOutputs(self):
        self.output.SetData(self.input.GetData())
        super().UpdateOutputs()


class NumberOperation(LogicBlock):
    def __init__(self, operation):
        super().__init__()
        self.output = self.AddOutput("Out", float)
        self.inputA = self.AddInput("A", float)
        self.inputB = self.AddInput("B", float)
        self.operation = operation

    def UpdateOutputs(self):
        self.output.SetData(self.operation(self.inputA.GetData(), self.inputB.GetData()))
        super().UpdateOutputs()


class Add(NumberOperation):
    def __init__(self):
        super().__init__(lambda a, b: a + b)

    def GetName(self=None):
        return "Add (A+B)"


class Subtract(NumberOperation):
    def __init__(self):
        super().__init__(lambda a, b: a - b)

    def GetName(self=None):
        return "Subtract (A-B)"


class Multiply(NumberOperation):
    def GetName(self=None):
        return "Multiply (A*B)"

    def __init__(self):
        super().__init__(lambda a, b: a * b)


class Divide(NumberOperation):
    def GetName(self=None):
        return "Divide (A/B)"

    def __init__(self):
        super().__init__(lambda a, b: a / b)

    def UpdateOutputs(self):
        if self.inputB.GetData() == 0:
            self.output.SetData(0)
            LogicBlock.UpdateOutputs(self)
        else:
            super().UpdateOutputs()


class Modulus(NumberOperation):
    def GetName(self=None):
        return "Modulus (A/B remainder)"

    def __init__(self):
        super().__init__(lambda a, b: a % b)

    def UpdateOutputs(self):
        if self.inputB.GetData() == 0:
            self.output.SetData(0)
            LogicBlock.UpdateOutputs(self)
        else:
            super().UpdateOutputs()


class Exponent(NumberOperation):
    def GetName(self=None):
        return "Exponent (A^B)"

    def __init__(self):
        super().__init__(lambda a, b: math.pow(a, b))


class LShift(LogicBlock):
    def GetName(self=None):
        return "Left Shift (A<<B)"

    def __init__(self):
        super().__init__()
        self.output = self.AddOutput("Out", int)
        self.inputA = self.AddInput("A", int)
        self.inputB = self.AddInput("B", int)

    def UpdateOutputs(self):
        self.output.SetData(self.inputA.GetData() << self.inputB.GetData())


class RShift(LogicBlock):
    def GetName(self=None):
        return "Right Shift (A>>B)"

    def __init__(self):
        super().__init__()
        self.output = self.AddOutput("Out", int)
        self.inputA = self.AddInput("A", int)
        self.inputB = self.AddInput("B", int)

    def UpdateOutputs(self):
        self.output.SetData(self.inputA.GetData() >> self.inputB.GetData())


class BAnd(LogicBlock):
    def GetName(self=None):
        return "Bitwise-AND (A&B)"

    def __init__(self):
        super().__init__()
        self.output = self.AddOutput("Out", int)
        self.inputA = self.AddInput("A", int)
        self.inputB = self.AddInput("B", int)

    def UpdateOutputs(self):
        self.output.SetData(self.inputA.GetData() & self.inputB.GetData())


class BOr(LogicBlock):
    def GetName(self=None):
        return "Bitwise-OR (A|B)"

    def __init__(self):
        super().__init__()
        self.output = self.AddOutput("Out", int)
        self.inputA = self.AddInput("A", int)
        self.inputB = self.AddInput("B", int)

    def UpdateOutputs(self):
        self.output.SetData(self.inputA.GetData() | self.inputB.GetData())


class BNot(LogicBlock):
    def GetName(self=None):
        return "Bitwise-Not (~In)"

    def __init__(self):
        super().__init__()
        self.output = self.AddOutput("Out", int)
        self.inputA = self.AddInput("In", int)

    def UpdateOutputs(self):
        self.output.SetData(~self.inputA.GetData())


class Round(LogicBlock):
    def GetName(self=None):
        return "Round"

    def __init__(self):
        super().__init__()
        self.output = self.AddOutput("Out", int)
        self.input = self.AddInput("In", float)

    def UpdateOutputs(self):
        self.output.SetData(round(self.input.GetData()))
        super().UpdateOutputs()


class Ceiling(LogicBlock):
    def GetName(self=None):
        return "Ceiling (Nearest larger integer)"

    def __init__(self):
        super().__init__()
        self.output = self.AddOutput("Out", int)
        self.input = self.AddInput("In", float)

    def UpdateOutputs(self):
        self.output.SetData(math.ceil(self.input.GetData()))
        super().UpdateOutputs()


class Floor(LogicBlock):
    def GetName(self=None):
        return "Floor (Nearest smaller integer)"

    def __init__(self):
        super().__init__()
        self.output = self.AddOutput("Out", int)
        self.input = self.AddInput("In", float)

    def UpdateOutputs(self):
        self.output.SetData(math.floor(self.input.GetData()))
        super().UpdateOutputs()


class Time(LogicBlock):
    def GetName(self=None):
        return "Time"

    programStartTime = time.time()

    def __init__(self):
        super().__init__()
        self.output = self.AddOutput("Time since start (seconds)", float)

    def UpdateOutputs(self):
        self.output.SetData(time.time() - Time.programStartTime)
        super().UpdateOutputs()
