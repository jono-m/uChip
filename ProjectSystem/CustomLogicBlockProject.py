from Project import Project
from ProjectEntity import ProjectEntity
from BlockSystemEntity import BlockSystemEntity
from BlockSystem.CompoundLogicBlock import CompoundLogicBlock


class CustomLogicBlockProject(Project):
    def __init__(self):
        super().__init__()

        self._customLogicBlock = CompoundLogicBlock()

    def GetCustomLogicBlock(self):
        return self._customLogicBlock

    def AddEntity(self, entity: ProjectEntity):
        super().AddEntity(entity)
        if isinstance(entity, BlockSystemEntity):
            self._customLogicBlock.AddSubBlock(entity.GetBlock())

    def RemoveEntity(self, entity: ProjectEntity):
        super().RemoveEntity(entity)
        if isinstance(entity, BlockSystemEntity):
            self._customLogicBlock.RemoveSubBlock(entity.GetBlock())
