import typing
from enum import Enum, auto


class Program:
    def __init__(self):
        self.parameters = []
        self.name = "New Program"
        self.logicBlocks = []
        self.steps = []
        self.startStep = StartStep()
        self.endStep = EndStep()


class Step:
    def __init__(self):
        self.name = "Step"
        self.completedPorts = []
        self.inputPorts = []


class StartStep(Step):
    def __init__(self):
        super().__init__()
        self.name = "Start"
        self.completedPorts.append(CompletedPort())


class EndStep(Step):
    def __init__(self):
        super().__init__()
        self.name = "Stop"
        self.completedPorts.append(CompletedPort())


class WaitStep(Step):
    def __init__(self):
        super().__init__()
        self.name = "Wait"
        self.completedPorts.append(CompletedPort())
        self.waitingInput = InputPort()
        self.waitingInput.dataType = Data.DataType.NUMBER
        self.inputPorts.append()


class LogicBlock:
    def __init__(self):
        self.name = "Logic Block"
        self.inputPorts = []
        self.outputPorts = []


class InputPort:
    def __init__(self):
        self.name = "Input"
        self.parameter = Data.DataType.NUMBER
        self.connectedOutput = None


class OutputPort:
    def __init__(self):
        self.name = "Output"
        self.dataType = Data.DataType.NUMBER
        self.connectedInputs = []


class CompletedPort:
    def __init__(self):
        self.name = "Completed"
        self.nextSteps = []


class Data:
    class DataType(Enum):
        NUMBER = auto()
        BOOLEAN = auto()
        OPTION = auto()
        VALVE = auto()

    def __init__(self, value):
        self.value = value


class Input:
    def __init__(self):
        self.name = "New Input"
        self.defaultNumber = 0
        self.defaultBoolean = False
        self.defaultOption = 0

        self.type = Data.DataType.NUMBER

        self.minimumValue = None
        self.valueStep = 0
        self.maximumValue = None
        self.integersOnly = False

        self.options = ["New Option"]


class InputValue:
    def __init__(self, value):
        self.value = value
