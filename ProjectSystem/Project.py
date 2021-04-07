from ProjectEntity import ProjectEntity
from pathlib import Path
from FileTrackingObject import FileTrackingObject
import typing
import dill


class ProjectFileError(Exception):
    pass


class Project:
    def __init__(self):
        self._entities: typing.List[ProjectEntity] = []

        self._projectPath: typing.Optional[Path] = None

    def GetProjectName(self):
        return self._projectPath.stem

    def GetProjectPath(self):
        return self._projectPath

    def GetEntities(self):
        return self._entities

    def AddEntity(self, entity: ProjectEntity):
        if entity not in self._entities:
            entity.OnEntityAdded()
            self._entities.append(entity)

    def RemoveEntity(self, entity: ProjectEntity):
        if entity in self._entities:
            entity.OnEntityRemoved()
            self._entities.remove(entity)

    def Save(self, path: Path):
        lastPath = self._projectPath

        self._projectPath = path

        self.ConvertAllPaths(True)

        try:
            file = open(self._projectPath, "wb")
            dill.dump(self, file)
            file.close()
        except Exception as e:
            self._projectPath = lastPath
            raise ProjectFileError("Could not save file to " + str(path.resolve()) + ".\nError:" + str(e))

        self.ConvertAllPaths(False)

    @staticmethod
    def LoadFromFile(path: Path) -> 'Project':
        if not path.exists():
            raise ProjectFileError("Could not find file " + str(path.resolve()) + ".")

        try:
            file = open(path, "rb")
            loadedProject: 'Project' = dill.load(file)
            file.close()
        except Exception as e:
            raise ProjectFileError("Could not load file " + str(path.resolve()) + ".\nError:" + str(e))

        loadedProject._projectPath = path

        loadedProject.OnLoaded()

        return loadedProject

    def OnLoaded(self):
        self.ConvertAllPaths(False)

    def ConvertAllPaths(self, toRelative):
        for entity in self._entities:
            for name in entity.editableProperties:
                editableProperty = entity.editableProperties[name]
                if isinstance(editableProperty, FileTrackingObject):
                    editableProperty.pathToLoad = self.ConvertPath(editableProperty.pathToLoad, toRelative)
                if isinstance(editableProperty, Path):
                    entity.editableProperties[name] = self.ConvertPath(editableProperty, toRelative)

    def ConvertPath(self, child: Path, toRelative):
        if toRelative:
            return child.relative_to(self._projectPath)
        else:
            return self._projectPath / child
