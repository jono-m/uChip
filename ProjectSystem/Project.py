from BlockSystem.LogicBlocks import OutputLogicBlock
from ProjectSystem.BlockSystemEntity import BlockSystemEntity
from BlockSystem.DataPorts import InputPort
from BlockSystem.Data import Data
from ProjectEntity import ProjectEntity
from pathlib import Path
from FileTracker import FileTracker
import typing
import dill


class ProjectFileError(Exception):
    pass


class Project:
    _T = typing.TypeVar('_T', bound=ProjectEntity)

    def __init__(self):
        self._entities: typing.List[ProjectEntity] = []

        self._inputs: typing.List[Data] = []
        self._settings: typing.List[Data] = []
        self._projectPath: typing.Optional[Path] = None

    def GetProjectName(self):
        return self._projectPath.stem

    def GetProjectPath(self):
        return self._projectPath

    def GetEntities(self):
        return self._entities

    def GetOutputs(self):
        return [block.GetOutput() for block in self.GetProjectBlocks() if
                isinstance(block, OutputLogicBlock)]

    def GetInputs(self):
        return self._inputs

    def GetSettings(self):
        return self._settings

    def AddInput(self, inputData: Data):
        if inputData not in self._inputs:
            self._inputs.append(inputData)
        return inputData

    def RemoveInput(self, inputData: Data):
        if inputData in self._inputs:
            self._inputs.remove(inputData)

    def AddSetting(self, setting: Data):
        if setting not in self._settings:
            self._settings.append(setting)
        return setting

    def RemoveSetting(self, setting: Data):
        if setting in self._settings:
            self._settings.remove(setting)

    def GetProjectBlocks(self):
        return [entity.GetBlock() for entity in self.GetEntities() if isinstance(entity, BlockSystemEntity)]

    def UpdateBlocks(self):
        blocksWaitingForUpdate = self.GetProjectBlocks()
        while blocksWaitingForUpdate:
            blocksReadyForUpdate = []
            for blockWaitingForUpdate in blocksWaitingForUpdate:
                parentBlocks = [port.GetOwnerBlock() for port in blockWaitingForUpdate.GetPorts(InputPort)]
                areAllParentsUpdated = all([parentBlock not in blocksWaitingForUpdate for parentBlock in parentBlocks])
                if areAllParentsUpdated:
                    blocksReadyForUpdate.append(blockWaitingForUpdate)

            for blockReadyForUpdate in blocksReadyForUpdate:
                blocksWaitingForUpdate.remove(blockReadyForUpdate)
                blockReadyForUpdate.Update()

    def AddEntity(self, entity: _T) -> _T:
        if entity not in self._entities:
            entity.OnEntityAdded()
            self._entities.append(entity)
        return entity

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
                if isinstance(editableProperty, FileTracker):
                    editableProperty.pathToLoad = self.ConvertPath(editableProperty.pathToLoad, toRelative)
                if isinstance(editableProperty, Path):
                    entity.editableProperties[name] = self.ConvertPath(editableProperty, toRelative)

    def ConvertPath(self, child: Path, toRelative):
        if toRelative:
            return child.relative_to(self._projectPath)
        else:
            return self._projectPath / child
