from BlockSystemEntity import BlockSystemEntity, GraphBlock
from GraphSystem.ProjectBlock import ProjectBlock
from ProjectTypes.Project import Project
from pathlib import Path
from FileTracker import FileTracker


class ProjectBlockFileTracker(FileTracker):
    def __init__(self, path: Path, block: ProjectBlock):
        self._projectBlock = block
        super().__init__(path)

    def ReportError(self, error: str):
        super().ReportError(error)
        self._projectBlock.SetInvalid(error)

    def GetProjectBlock(self):
        return self._projectBlock

    def TryReload(self) -> bool:
        if not super().TryReload():
            return False
        try:
            newProject = Project.LoadFromFile(self.pathToLoad)
        except Exception as e:
            self.ReportError("Error loading project file: \n" + str(e))
            return False
        try:
            self._projectBlock.LoadProject(newProject)
        except Exception as e:
            self.ReportError("Error loading project:\n" + str(e))
            return False
        return True

    def OnSyncedSuccessfully(self):
        super().OnSyncedSuccessfully()
        self._projectBlock.SetValid()


class ProjectBlockEntity(BlockSystemEntity):
    def __init__(self, path: Path, block: ProjectBlock):
        super().__init__(block)

        self.editableProperties['blockProjectFile'] = ProjectBlockFileTracker(path, block)

    def GetBlock(self) -> GraphBlock:
        self.editableProperties['blockProjectFile'].Sync()
        return self.editableProperties['blockProjectFile'].GetProjectBlock()
