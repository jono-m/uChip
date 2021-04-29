import typing

Parameters = typing.List[typing.Tuple[str, 'ParameterDescription']]
ParameterValues = typing.List[typing.Tuple[str, 'ParameterValue']]


class Program:
    def __init__(self):
        self.name = "Unnamed Program"
        self.parameters: Parameters = []


class ProgramInstance:
    def __init__(self, program: Program):
        self.program = program
        self.parameterValues = 
        self.isRunning = False


class ProgramButton:
    def __init__(self, program: Program):
        self.programInstance = ProgramInstance(program)


class ParameterDescription:
    def __init__(self, initialDefaultValue):
        self.defaultValue = initialDefaultValue


class BooleanParameterDescription(ParameterDescription):
    def __init__(self):
        super().__init__(False)


class NumberParameterDescription(ParameterDescription):
    def __init__(self):
        super().__init__(0)
        self.minimum = None
        self.maximum = None
        self.step = None
        self.isInteger = False


class ValveParameterDescription(ParameterDescription):
    def __init__(self):
        super().__init__(None)


class OptionParameterDescription(ParameterDescription):
    def __init__(self):
        super().__init__(0)
        self.options = ["Option 1"]


class ParameterValue:
    def __init__(self, value, description: ParameterDescription):
        self.value = value
        self.description = description
