from Project import Project
from pathlib import Path
import typing


class ProjectEntity:
    def __init__(self):
        self.editableProperties: typing.Dict[str, object] = {'Position': (0, 0)}

    def GetPosition(self):
        return self.editableProperties['Position']

    def SetPosition(self, position: typing.Tuple[float, float]):
        self.editableProperties['Position'] = position
