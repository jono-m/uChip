import time
from BaseLogicBlock import BaseLogicBlock
from Util import DatatypeToName
from BlockSystem.BaseConnectableBlock import Parameter
import math
import typing


class ConstantBlock(BaseLogicBlock):
    def __init__(self, dataType: typing.Union[typing.Type, typing.List]):
        super().__init__()

        self.value = self.AddParameter(Parameter("Value: ", dataType))
        self.output = self.CreateOutputPort("Out", dataType)

    def GetName(self) -> str:
        return DatatypeToName(self.value.dataType) + " Constant"

    def Update(self):
        super().Update()
        self.output.SetValue(self.value.GetValue())


class UnaryOperationBlock(BaseLogicBlock):
    def __init__(self, operation, dataType=float, outDataType=None):
        super().__init__()
        if outDataType is None:
            outDataType = dataType
        self.output = self.CreateOutputPort("Out", outDataType)
        self.inputA = self.CreateInputPort("In", dataType)
        self.operation = operation

    def Update(self):
        super().Update()
        try:
            self.output.SetValue(self.operation(self.inputA.GetValue()))
        except ArithmeticError:
            self.output.SetValue(0)


class BinaryOperationBlock(BaseLogicBlock):
    def __init__(self, operation, dataType=float, outDataType=None):
        super().__init__()
        if outDataType is None:
            outDataType = dataType
        self.output = self.CreateOutputPort("Out", outDataType)
        self.inputA = self.CreateInputPort("A", dataType)
        self.inputB = self.CreateInputPort("B", dataType)
        self.operation = operation

    def Update(self):
        super().Update()
        try:
            self.output.SetValue(self.operation(self.inputA.GetValue(), self.inputB.GetValue()))
        except ArithmeticError:
            self.output.SetValue(0)


class Add(BinaryOperationBlock):
    def __init__(self):
        super().__init__(lambda a, b: a + b)

    def GetName(self):
        return "Add (A+B)"


class Subtract(BinaryOperationBlock):
    def __init__(self):
        super().__init__(lambda a, b: a - b)

    def GetName(self):
        return "Subtract (A-B)"


class Multiply(BinaryOperationBlock):
    def GetName(self):
        return "Multiply (A*B)"

    def __init__(self):
        super().__init__(lambda a, b: a * b)


class Divide(BinaryOperationBlock):
    def GetName(self):
        return "Divide (A/B)"

    def __init__(self):
        super().__init__(lambda a, b: a / b)


class Modulus(BinaryOperationBlock):
    def GetName(self):
        return "Modulus (A/B remainder)"

    def __init__(self):
        super().__init__(lambda a, b: a % b)


class Exponent(BinaryOperationBlock):
    def GetName(self):
        return "Exponent (A^B)"

    def __init__(self):
        super().__init__(lambda a, b: math.pow(a, b))


class BitwiseOperation(BinaryOperationBlock):
    def GetName(self):
        return "Bitwise " + self.modeParameter.dataType[self.modeParameter.GetValue()]

    def __init__(self):
        super().__init__(self.DoOperation, int)

        self.modeParameter = self.CreateParameter("Operation", ["A << B",
                                                                "A >> B",
                                                                "A & B",
                                                                "A | B",
                                                                "A ^ B"])

    def DoOperation(self, A: int, B: int):
        return eval(self.modeParameter.dataType[self.modeParameter.GetValue()])


class Round(UnaryOperationBlock):
    def GetName(self):
        return "Round"

    def __init__(self):
        super().__init__(lambda a: round(a), float, int)


class Ceiling(UnaryOperationBlock):
    def GetName(self):
        return "Ceiling (Nearest larger integer)"

    def __init__(self):
        super().__init__(lambda a: math.ceil(a), float, int)


class Floor(UnaryOperationBlock):
    def GetName(self):
        return "Floor (Nearest smaller integer)"

    def __init__(self):
        super().__init__(lambda a: math.floor(a), float, int)

class BooleanOperation(BinaryOperationBlock):
    def GetName(self):
        return "Boolean (" + self.

    def __init__(self):
        super().__init__(self.DoOperation, bool)

        self.modeParameter = self.CreateParameter("Operation", ["A and B",
                                                                "A or B",
                                                                "A xor B",
                                                                "A | B",
                                                                "A ^ B"])

    def DoOperation


class Or(BinaryOperationBlock):
    def GetName(self):
        return "Or"

    def __init__(self):
        super().__init__(lambda a, b: a or b, bool)


class Not(UnaryOperationBlock):
    def GetName(self):
        return "Not"

    def __init__(self):
        super().__init__(lambda a: not a, bool)


class Equals(BinaryOperationBlock):
    def GetName(self):
        return "A equals (==) B"

    def __init__(self):
        super().__init__(lambda a, b: a == b, float, bool)


class NEqualsBlock(BinaryOperationBlock):
    def GetName(self):
        return "A does not equal (!=) B"

    def __init__(self):
        super().__init__(lambda a, b: a != b, float, bool)


class LThanBlock(BinaryOperationBlock):
    def GetName(self):
        return "A less than (<) B"

    def __init__(self):
        super().__init__(lambda a, b: a < b, float, bool)


class GThanBlock(BinaryOperationBlock):
    def GetName(self):
        return "A greater than (>) B"

    def __init__(self):
        super().__init__(lambda a, b: a > b, float, bool)


class LThanEBlock(BinaryOperationBlock):
    def GetName(self):
        return "A less than or equal to (<=) B"

    def __init__(self):
        super().__init__(lambda a, b: a <= b, float, bool)


class GThanEBlock(BinaryOperationBlock):
    def GetName(self):
        return "A greater than or equal to (>=) B"

    def __init__(self):
        super().__init__(lambda a, b: a >= b, float, bool)


class IfLogicBlock(BaseLogicBlock):
    def GetName(self):
        return "If/Else (Branch)"

    def __init__(self):
        super().__init__()
        self.output = self.CreateOutputPort("Out", None)
        self.conditionInput = self.CreateInputPort("Condition", bool)
        self.trueInput = self.CreateInputPort("If YES", None)
        self.falseInput = self.CreateInputPort("If NO", None)

    def Update(self):
        super().Update()
        if self.conditionInput.GetValue():
            self.output.SetValue(self.trueInput.GetValue())
        else:
            self.output.SetValue(self.falseInput.GetValue())


class TimeLogicBlock(BaseLogicBlock):
    def GetName(self):
        return "Time"

    programStartTime = time.time()

    def __init__(self):
        super().__init__()
        self.output = self.CreateOutputPort("Time since start (seconds)", float)

    def Update(self):
        super().Update()
        self.output.SetValue(time.time() - TimeLogicBlock.programStartTime)
