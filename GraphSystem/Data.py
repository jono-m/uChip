import typing

# This is the kind of data that can get passed around through the block system.

DataTypeSpec = typing.Union[typing.Type, typing.List, None]


class Data:
    def __init__(self, dataType: DataTypeSpec, initialValue=None):
        self.dataType = dataType

        if type(self.dataType) == list or self.dataType is None:
            self._value = 0
        else:
            self._value = dataType()

        if initialValue is not None:
            self.SetValue(initialValue)

    def Copy(self):
        return Data(self.dataType, self.GetValue())

    def GetValue(self):
        return self._value

    def SetValue(self, value):
        self._value = self.Cast(value)

    def Cast(self, value):
        if type(self.dataType) == list:
            return max(0, min(len(self.dataType) - 1, int(value)))
        elif self.dataType is None:
            return value
        else:
            return self.dataType(value)

    def GetDataTypeString(self) -> str:
        if self.dataType == list:
            return "Option"
        if self.dataType == int or self.dataType == float:
            return "Number"
        if self.dataType == str:
            return "Text"
        if self.dataType == bool:
            return "True/False"
        else:
            return str(self.dataType).split('\'')[1].capitalize()
