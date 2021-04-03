from ProjectEntity import ProjectEntity
from pathlib import Path
import typing


class Project:
    def __init__(self):
        self.entities: typing.List[ProjectEntity] = []

        self.savePath: typing.Optional[Path] = None

    def Save(self):
        for entity in self.entities:
            for name in entity.editableProperties:
                if isinstance(entity.editableProperties[Path]value, Path):

