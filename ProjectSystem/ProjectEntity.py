import typing


class ProjectEntity:
    def __init__(self):
        self.editableProperties: typing.Dict[str, typing.Any] = {'position': (0, 0)}

    def GetPosition(self):
        self.UpdateEntity()
        return self.editableProperties['position']

    def SetPosition(self, position: typing.Tuple[float, float]):
        self.editableProperties['position'] = position

    def UpdateEntity(self):
        pass
