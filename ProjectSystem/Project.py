from ProjectEntity import ProjectEntity
from pathlib import Path
from FileTracker import FileTracker
from enum import Enum, auto
import re
import typing
import dill
import io


class ProjectFileError(Exception):
    pass


class Project:
    _T = typing.TypeVar('_T', bound=ProjectEntity)

    def __init__(self, path: Path):
        self._entities: typing.List[ProjectEntity] = []
        self._path = path
        self._file: typing.Optional[io.FileIO] = None
        self.Create()

        self._modified = False

    def HasBeenModified(self):
        return self._modified

    def RegisterModification(self):
        self._modified = True

    def GetProjectName(self):
        return " ".join(re.sub(r"(([A-Z]+)|([0-9]+))", r" \1", re.sub(r"[_.-]", " ", self._path.stem)).split()).title()

    def GetProjectPath(self):
        return self._path

    def GetEntities(self):
        return self._entities

    def AddEntity(self, entity: _T) -> _T:
        if entity not in self._entities:
            self._entities.append(entity)
        return entity

    def RemoveEntity(self, entity: ProjectEntity):
        if entity in self._entities:
            self._entities.remove(entity)

    def Create(self):
        if self._file is not None:
            raise ProjectFileError("Project is already open.")
        try:
            self._file = open(self._path, "xb+")
        except Exception as e:
            raise ProjectFileError("Could not create file '" + str(self._path.absolute()) + ".\nError:" + str(e))
        self.Save()

    def SaveAs(self, path: Path):
        lastPath = self._path
        lastFile = self._file

        self._path = path
        self._file = None

        try:
            self.Create()
        except Exception as e:
            self._path = lastPath
            self._file = lastFile
            raise e

        if lastFile is not None:
            lastFile.close()

    def Save(self):
        if self._file is None:
            raise ProjectFileError("Project is not yet opened.")

        self.ConvertAllPaths(Project.ConvertMode.TO_RELATIVE)

        tempFile: io.FileIO = self._file
        self._file = None
        try:
            binaryContainer = io.BytesIO()
            dill.dump(self, binaryContainer)
            tempFile.truncate(0)
            tempFile.write(binaryContainer.getvalue())
        except Exception as e:
            raise ProjectFileError("Could not save file to " + str(self._path.resolve()) + ".\nError:" + str(e))
        finally:
            self._file = tempFile
            self.ConvertAllPaths(Project.ConvertMode.TO_ABSOLUTE)

        self._modified = False

    def Close(self):
        if self._file is not None:
            self._file.close()

    @staticmethod
    def Open(path: Path) -> 'Project':
        if not path.exists():
            raise ProjectFileError("Could not find file " + str(path.resolve()) + ".")

        try:
            file = open(path, "rb+")
            loadedProject: 'Project' = dill.load(file)
        except Exception as e:
            raise ProjectFileError("Could not load file " + str(path.resolve()) + ".\nError:" + str(e))

        loadedProject._path = path
        loadedProject._file = file

        loadedProject.ConvertAllPaths(Project.ConvertMode.TO_ABSOLUTE)

        return loadedProject

    class ConvertMode(Enum):
        TO_RELATIVE = auto()
        TO_ABSOLUTE = auto()

    def ConvertAllPaths(self, mode: ConvertMode):
        for entity in self._entities:
            for name in entity.editableProperties:
                editableProperty = entity.editableProperties[name]
                if isinstance(editableProperty, FileTracker):
                    editableProperty.pathToLoad = self.ConvertPath(editableProperty.pathToLoad, mode)
                if isinstance(editableProperty, Path):
                    entity.editableProperties[name] = self.ConvertPath(editableProperty, mode)

    def ConvertPath(self, child: Path, mode: ConvertMode):
        if mode is Project.ConvertMode.TO_RELATIVE:
            return child.relative_to(self._path)
        elif mode is Project.ConvertMode.TO_ABSOLUTE:
            return self._path / child
