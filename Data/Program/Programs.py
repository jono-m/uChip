from typing import List, Dict, Any, Optional
from enum import Enum, auto


class ProgramSpecification:
    def __init__(self):
        self.parameters: List[Parameter] = []
        self.name = "New Program"
        self.description = ""
        self.script = """"""


class ParameterType(Enum):
    INTEGER = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    STRING = auto()
    VALVE = auto()
    PROGRAM = auto()
    LIST = auto()
    CUSTOM = auto()

    def GetInitialValue(self):
        return {ParameterType.INTEGER: 0,
                ParameterType.FLOAT: 0.0,
                ParameterType.BOOLEAN: False,
                ParameterType.STRING: "",
                ParameterType.VALVE: None,
                ParameterType.PROGRAM: None,
                ParameterType.LIST: [],
                ParameterType.CUSTOM: None}[self]

    def ToString(self):
        return {ParameterType.INTEGER: "Integer",
                ParameterType.FLOAT: "Float",
                ParameterType.BOOLEAN: "Boolean",
                ParameterType.STRING: "String",
                ParameterType.VALVE: "Valve",
                ParameterType.PROGRAM: "Program",
                ParameterType.LIST: "List",
                ParameterType.CUSTOM: "Other"}[self]


class Parameter:
    def __init__(self):
        self.name = "New Parameter"
        self.dataType = ParameterType.INTEGER

        self.defaultValues = {dataType: dataType.GetDefaultValue() for dataType in ParameterType}

        self.hasMinimum = False
        self.hasMaximum = False
        self.minimum = 0
        self.maximum = 100
        self.listType = ParameterType.INTEGER


class ProgramInstance:
    def __init__(self):
        self.parameterValues: Dict[Parameter, Dict[ParameterType, Any]] = {}
        self.specification: Optional[ProgramSpecification] = None
        self.parameterVisibility: Dict[Parameter, bool] = {}
        self.position_x = 0
        self.position_y = 0
        self.name = ""
        self.showDescription = True

def InstantiateProgram(program: ProgramSpecification):
    instance = ProgramInstance()
    instance.parameterValues = {parameter: parameter.defaultValues}