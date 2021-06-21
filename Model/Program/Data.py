from enum import Enum, auto
from typing import Any

DataValueType = Any


class DataType(Enum):
    INTEGER = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    STRING = auto()
    VALVE = auto()
    PROGRAM_PRESET = auto()
    LIST = auto()
    OTHER = auto()

    def GetDefaultValue(self):
        return {DataType.INTEGER: 0,
                DataType.FLOAT: 0.0,
                DataType.BOOLEAN: False,
                DataType.STRING: "",
                DataType.VALVE: None,
                DataType.PROGRAM_PRESET: None,
                DataType.LIST: [],
                DataType.OTHER: None}[self]

    def ToString(self):
        return {DataType.INTEGER: "Integer",
                DataType.FLOAT: "Float",
                DataType.BOOLEAN: "Boolean",
                DataType.STRING: "String",
                DataType.VALVE: "Valve",
                DataType.PROGRAM_PRESET: "Program Preset",
                DataType.LIST: "List",
                DataType.OTHER: "Other"}[self]
