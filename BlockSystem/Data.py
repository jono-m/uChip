import typing

# This is the kind of data that can get passed around through the block system.

DataTypeSpec = typing.Union[typing.Type, typing.List, None]


class Data:
    def __init__(self, name: str, dataType: DataTypeSpec, initialValue=None):
        self.dataType = dataType
        self._name = name

        if type(self.dataType) == list or self.dataType is None:
            self._value = 0
        else:
            self._value = dataType()

        if initialValue is not None:
            self.SetValue(initialValue)

    def Copy(self):
        return Data(self.GetName(), self.dataType, self.GetValue())

    def SetName(self, name: str):
        self._name = name

    def GetName(self):
        return self._name

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


def MatchData(newDataList: typing.List[Data], oldDataList: typing.List[Data]) -> \
        (typing.List[(Data, Data)], typing.List[Data], typing.List[Data]):
    matches = []
    for newData in newDataList.copy():
        for oldData in oldDataList:
            if newData.GetName() == oldData.GetName() and newData.dataType == oldData.dataType:
                matches.append((newData, oldData))
                newDataList.remove(newData)
                oldDataList.remove(oldData)
                break

    return matches, newDataList, oldDataList
