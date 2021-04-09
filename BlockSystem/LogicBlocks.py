import time
from BaseConnectableBlock import BaseConnectableBlock
from DataPorts import InputPort, OutputPort
from BlockSystem.Data import Data, DataTypeSpec
import math


class ConstantBlock(BaseConnectableBlock):
    def __init__(self, dataType: DataTypeSpec):
        super().__init__()

        self.value = self.AddSetting(Data("Value: ", dataType))
        self.output = self.AddPort(OutputPort(Data("Out", dataType)))

    def GetName(self) -> str:
        return self.value.data.GetDataTypeString() + " Constant"

    def Update(self):
        super().Update()
        self.output.SetValue(self.value.GetValue())


class UnaryOperationBlock(BaseConnectableBlock):
    def __init__(self, operation, dataType=float, outDataType=None):
        super().__init__()
        if outDataType is None:
            outDataType = dataType
        self.output = self.AddPort(OutputPort(Data("Out", outDataType)))
        self.inputA = self.AddPort(InputPort(Data("In", dataType)))
        self.operation = operation

    def Update(self):
        super().Update()
        try:
            self.output.SetValue(self.operation(self.inputA.GetValue()))
        except ArithmeticError:
            self.output.SetValue(0)


class BinaryOperationBlock(BaseConnectableBlock):
    def __init__(self, operation, dataType=float, outDataType=None):
        super().__init__()
        if outDataType is None:
            outDataType = dataType
        self.output = self.AddPort(OutputPort(Data("Out", outDataType)))
        self.inputA = self.AddPort(InputPort(Data("A", dataType)))
        self.inputB = self.AddPort(InputPort(Data("B", dataType)))
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

        self.modeParameter = self.AddSetting(Data("Operation", ["A << B",
                                                                "A >> B",
                                                                "A & B",
                                                                "A | B",
                                                                "A ^ B"]))

    def DoOperation(self, A: int, B: int):
        return eval(self.modeParameter.dataType[self.modeParameter.GetValue()], {'A': A, 'B': B})


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
        return "Boolean (" + self.modeParameter.dataType[self.modeParameter.GetValue()] + ")"

    def __init__(self):
        super().__init__(self.DoOperation, bool)

        self.modeParameter = self.AddSetting(Data("Operation", ["A and B",
                                                                "A or B"]))

    def DoOperation(self, A: int, B: int):
        return eval(self.modeParameter.dataType[self.modeParameter.GetValue()], {'A': A, 'B': B})


class Not(UnaryOperationBlock):
    def GetName(self):
        return "Not"

    def __init__(self):
        super().__init__(lambda a: not a, bool)


class ComparisonOperation(BinaryOperationBlock):
    def GetName(self):
        return "Comparison (" + self.modeParameter.dataType[self.modeParameter.GetValue()] + ")"

    def __init__(self):
        super().__init__(self.DoOperation, float, bool)

        self.modeParameter = self.AddSetting(Data("Operation", ["A == B",
                                                                "A != B",
                                                                "A < B",
                                                                "A <= B",
                                                                "A > B",
                                                                "A >= B"]))

    def DoOperation(self, A: int, B: int):
        return eval(self.modeParameter.dataType[self.modeParameter.GetValue()], {'A': A, 'B': B})


class IfLogicBlock(BaseConnectableBlock):
    def GetName(self):
        return "If/Else (Branch)"

    def __init__(self):
        super().__init__()
        self.output = self.AddPort(OutputPort(Data("Out", None)))
        self.conditionInput = self.AddPort(InputPort(Data("Condition", bool)))
        self.trueInput = self.AddPort(InputPort(Data("If YES", None)))
        self.falseInput = self.AddPort(InputPort(Data("If NO", None)))

    def Update(self):
        super().Update()
        if self.conditionInput.GetValue():
            self.output.SetValue(self.trueInput.GetValue())
        else:
            self.output.SetValue(self.falseInput.GetValue())


class TimeLogicBlock(BaseConnectableBlock):
    def GetName(self):
        return "Time"

    programStartTime = time.time()

    def __init__(self):
        super().__init__()
        self.output = self.AddPort(OutputPort(Data("Time since start (seconds)", float)))

    def Update(self):
        super().Update()
        self.output.SetValue(time.time() - TimeLogicBlock.programStartTime)


# Logic block that represents an input to a project
class InputBlock(BaseConnectableBlock):
    def __init__(self, input: Data):
        super().__init__()
        self._outputPort = self.AddPort(OutputPort(Data("Value", input.dataType)))
        self._input = input

    def GetName(self):
        return "Input: " + self._input.GetName()

    def Update(self):
        super().Update()
        self._outputPort.SetValue(self._input.GetValue())


# Logic block that represents an output from a project
class SettingBlock(BaseConnectableBlock):
    def __init__(self, setting: Data):
        super().__init__()
        self._outputPort = self.AddPort(OutputPort(Data("Value", setting.dataType)))
        self._setting = setting

    def GetName(self):
        return "Setting: " + self._setting.GetName()

    def Update(self):
        super().Update()
        self._outputPort.SetValue(self._setting.GetValue())


# Logic block that represents an output from a project
class OutputLogicBlock(BaseConnectableBlock):
    def __init__(self, output: Data):
        super().__init__()
        self._output = output
        self._nameSetting = self.AddSetting(Data("Name", str, "New " + output.GetDataTypeString() + " Output"))
        self._inputPort = self.AddPort(InputPort(Data("Value", output.dataType)))

    def GetOutput(self):
        return self._output

    def GetName(self) -> str:
        return "Output: " + self._nameSetting.GetValue()

    def Update(self):
        super().Update()
        self._output.SetName(self._nameSetting.GetValue())
        self._output.SetValue(self._inputPort.GetValue())
