from enum import Enum, auto
from typing import Union

DataValueType = Union[int, float, bool]


class DataType(Enum):
    INTEGER = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    UNKNOWN = auto()

    def GetDefaultValue(self):
        return self.Cast(0)

    def Cast(self, value: DataValueType):
        return {DataType.INTEGER: int(value),
                DataType.FLOAT: float(value),
                DataType.BOOLEAN: bool(value),
                DataType.UNKNOWN: value}[self]
