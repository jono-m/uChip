from BlockSystemEntity import BlockSystemEntity, BaseConnectableBlock
from BlockSystem.ProjectLogicBlock import ProjectLogicBlock
from ProjectSystem.Project import Project
from pathlib import Path
from FileTrackingObject import FileTrackingObject


class ProjectLogicBlockFile(FileTrackingObject):
    def __init__(self, path: Path, block: ProjectLogicBlock):
        self._projectLogicBlock = block
        super().__init__(path)

    def ReportError(self, error: str):
        super().ReportError(error)
        self._projectLogicBlock.SetInvalid(error)

    def GetProjectLogicBlock(self):
        return self._projectLogicBlock

    def TryReload(self) -> bool:
        if not super().TryReload():
            return False
        try:
            newProject = Project.LoadFromFile(self.pathToLoad)
        except Exception as e:
            self.ReportError("Error loading project file: \n" + str(e))
            return False
        try:
            self._projectLogicBlock.LoadProject(newProject)
        except Exception as e:
            self.ReportError("Error loading project:\n" + str(e))
            return False
        return True

    def OnSyncedSuccessfully(self):
        super().OnSyncedSuccessfully()
        self._projectLogicBlock.SetValid()


class ProjectLogicBlockEntity(BlockSystemEntity):
    def __init__(self, path: Path, block: ProjectLogicBlock):
        super().__init__(block)

        self.editableProperties['blockProjectFile'] = ProjectLogicBlockFile(path, block)

    def GetBlock(self) -> BaseConnectableBlock:
        self.editableProperties['blockProjectFile'].Sync()
        return self.editableProperties['blockProjectFile'].GetProjectLogicBlock()