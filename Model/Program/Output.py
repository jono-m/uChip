from typing import Dict
from Data import DataType, DataValueType


class Output:
    def __init__(self, name="Output", dataType=DataType.INTEGER, initialValue=None):
        self._name = name
        self._dataType = dataType
        self._initialValue: Dict[DataType, DataValueType] = {dataType: dataType.GetDefaultValue() for dataType in
                                                             DataType}
        if initialValue:
            self.SetInitialValue(initialValue)

    def GetName(self):
        return self._name

    def SetName(self, name: str):
        self._name = name

    def GetDataType(self):
        return self._dataType

    def SetDataType(self, dataType: DataType):
        self._dataType = dataType

    def GetInitialValue(self):
        return self._initialValue[self._dataType]

    def SetInitialValue(self, value: DataValueType):
        self._initialValue[self._dataType] = self._dataType.Cast(value)
