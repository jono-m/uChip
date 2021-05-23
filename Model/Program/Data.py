from enum import Enum, auto
from typing import Union

DataValueType = Union[int, float, bool]


class DataType(Enum):
    INTEGER = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    STRING = auto()
    VALVE = auto()
    PROGRAM = auto()
    PROGRAM_PRESET = auto()

    def GetDefaultValue(self):
        return {DataType.INTEGER: 0,
                DataType.FLOAT: 0.0,
                DataType.BOOLEAN: False,
                DataType.STRING: "",
                DataType.VALVE: None,
                DataType.PROGRAM: None,
                DataType.PROGRAM_PRESET: None}[self]
