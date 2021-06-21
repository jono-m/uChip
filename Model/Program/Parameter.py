from typing import Optional, Dict

from Model.Program.Data import DataType, DataValueType


class Parameter:
    def __init__(self, name="New Parameter", dataType=DataType.INTEGER, defaultValue=None):
        self.name = name
        self.dataType: DataType = dataType

        self.defaultValueDict: Dict[DataType, DataValueType] = {dataType: dataType.GetDefaultValue() for dataType in
                                                                DataType}
        if defaultValue:
            self.defaultValueDict[dataType] = defaultValue

        self.minimumFloat: Optional[float] = 0
        self.maximumFloat: Optional[float] = 100
        self.minimumInteger: Optional[int] = 0
        self.maximumInteger: Optional[int] = 100
        self.listType = DataType.INTEGER

    def ValidateDefaultValues(self):
        self.defaultValueDict[DataType.INTEGER] = self.ClampInteger(self.defaultValueDict[DataType.INTEGER])
        self.defaultValueDict[DataType.FLOAT] = self.ClampFloat(self.defaultValueDict[DataType.FLOAT])

    def ClampInteger(self, integer: int):
        integer = max(integer, self.minimumInteger)
        integer = min(integer, self.maximumInteger)
        return integer

    def ClampFloat(self, floating: float):
        floating = max(floating, self.minimumFloat)
        floating = min(floating, self.maximumFloat)
        return floating
