from ProjectSystem.Project import Project
from CompoundLogicBlock import CompoundLogicBlock
from ProjectSystem.BlockSystemEntity import BlockSystemEntity
import typing


# A logic block basically just executes any logic block entities that are actively in a project.
# Used for running a chip project, testing out a logic block project,
# or for executing a custom logic block in another project.
class ProjectLogicBlock(CompoundLogicBlock):
    def GetName(self):
        if not self.IsValid():
            return "Invalid Project Block"
        return self._project.GetProjectName()

    def __init__(self):
        super().__init__()
        self._project: typing.Optional[Project] = None

    def IsValid(self):
        return super().IsValid() and self._project is not None

    def LoadProject(self, project: Project):
        self._project = project
        # Need to sync my connections
        self.SyncSubBlocks()

    def GetSubBlocks(self):
        self.SyncSubBlocks()
        return super().GetSubBlocks()

    def SyncSubBlocks(self):
        # TODO: Could probably optimize this strategy if performance is an issue.
        projectSubBlocks = [entity.GetBlock() for entity in self._project.GetEntities() if
                            isinstance(entity, BlockSystemEntity)]
        currentSubBlocks = super().GetSubBlocks()
        oldSubBlocks = [block for block in currentSubBlocks if block not in projectSubBlocks]
        newSubBlocks = [block for block in currentSubBlocks if block not in oldSubBlocks]
        [self.RemoveSubBlock(block) for block in oldSubBlocks]
        [self.AddSubBlock(block) for block in newSubBlocks]
