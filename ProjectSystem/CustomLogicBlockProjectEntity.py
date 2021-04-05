from CustomLogicBlockProject import CustomLogicBlockProject
from Project import ProjectFileError
from BlockSystemEntity import BlockSystemEntity
import typing
import os
from pathlib import Path


class CustomLogicBlockProjectEntity(BlockSystemEntity):
    def __init__(self, blockProject: CustomLogicBlockProject):
        super().__init__(blockProject.GetCustomLogicBlock())
        self._blockProject = blockProject

        self.editableProperties['customBlockPath'] = blockProject.GetProjectPath()
        self._attemptedLoadedVersion: typing.Optional[float] = os.path.getmtime(blockProject.GetProjectPath())
        self._attemptedLoadedPath: typing.Optional[float] = blockProject.GetProjectPath()

    def UpdateEntity(self):
        path: Path = self.editableProperties['customBlockPath']
        if not path.exists():
            self.GetBlock().SetInvalid("Cannot find file " + str(path.resolve()) + ".")
        elif path != self._attemptedLoadedPath or os.path.getmtime(path) > self._attemptedLoadedVersion:
            try:
                newBlockProject = CustomLogicBlockProject.LoadFromFile(path)
            except ProjectFileError as e:
                self.GetBlock().SetInvalid(str(e))

            self._attemptedLoadedPath = path
            self._attemptedLoadedVersion = os.path.getmtime(path)
