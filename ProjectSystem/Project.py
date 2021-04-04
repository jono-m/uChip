from ProjectEntity import ProjectEntity
from pathlib import Path
import typing
import dill


class Project:
    def __init__(self):
        self.entities: typing.List[ProjectEntity] = []

        self.projectPath: typing.Optional[Path] = None

    def Save(self):
        self.ConvertAllPaths(True)

        file = open(self.projectPath, "wb")
        dill.dump(self.entities, file)
        file.close()

        self.ConvertAllPaths(False)

    def LoadFromFile(self, path: Path):
        if not path.exists():
            return

        file = open(path, "rb")
        self.entities = dill.load(file)
        file.close()
        self.projectPath = path

        self.ConvertAllPaths(False)

    def ConvertAllPaths(self, toRelative):
        for entity in self.entities:
            for name in entity.editableProperties:
                editableProperty = entity.editableProperties[name]
                if isinstance(editableProperty, Path):
                    if toRelative:
                        entity.editableProperties[name] = editableProperty.relative_to(self.projectPath)
                    else:
                        entity.editableProperties[name] = self.projectPath / editableProperty
