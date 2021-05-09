from typing import Optional, Dict

from Data import DataType, DataValueType


class Parameter:
    def __init__(self, name="Parameter", dataType=DataType.INTEGER, defaultValue=None):
        self._name = name
        self._dataType: DataType = dataType

        self._defaultValue: Dict[DataType, DataValueType] = {dataType: dataType.GetDefaultValue() for dataType in
                                                             DataType}
        if defaultValue:
            self.SetDefaultValue(defaultValue)

        self._minimumFloat: Optional[float] = None
        self._maximumFloat: Optional[float] = None
        self._minimumInteger: Optional[int] = None
        self._maximumInteger: Optional[int] = None

    def SetName(self, name: str):
        self._name = name

    def GetName(self):
        return self._name

    def GetDataType(self):
        return self._dataType

    def SetDataType(self, newDataType: DataType):
        self._dataType = newDataType

    def GetIntegerBounds(self):
        return self._minimumInteger, self._maximumInteger

    def SetIntegerBounds(self, minimum: Optional[int], maximum: Optional[int]):
        self._minimumFloat = minimum
        self._maximumFloat = maximum
        self.Validate()

    def GetFloatBounds(self):
        return self._minimumFloat, self._maximumFloat

    def SetFloatBounds(self, minimum: Optional[float], maximum: Optional[float]):
        self._minimumFloat = minimum
        self._maximumFloat = maximum
        self.Validate()

    def GetDefaultValue(self):
        return self._defaultValue[self._dataType]

    def SetDefaultValue(self, value: DataValueType):
        self._defaultValue[self._dataType] = self._dataType.Cast(value)
        self.Validate()

    def Validate(self):
        self._defaultValue[DataType.INTEGER] = self.ClampInteger(self._defaultValue[DataType.INTEGER])
        self._defaultValue[DataType.FLOAT] = self.ClampFloat(self._defaultValue[DataType.FLOAT])

    def CastClamped(self, value: DataValueType):
        casted = self._dataType.Cast(value)
        if self._dataType is DataType.INTEGER:
            return self.ClampInteger(casted)
        if self._dataType is DataType.FLOAT:
            return self.ClampFloat(casted)
        return casted

    def ClampInteger(self, integer: int):
        if self._minimumInteger:
            integer = max(integer, self._minimumInteger)
        if self._maximumInteger:
            integer = max(integer, self._maximumInteger)
        return integer

    def ClampFloat(self, floating: float):
        if self._minimumFloat:
            floating = max(floating, self._minimumFloat)
        if self._maximumFloat:
            floating = max(floating, self._maximumFloat)
        return floating
