import typing

from ProjectSystem.Project import Project
from ProjectSystem.ProjectEntity import ProjectEntity
from ProjectSystem.BlockSystemEntity import BlockSystemEntity
from BlockSystem.LogicBlocks import ValveLogicBlock
from RigSystem.Rig import Rig
from BlockSystem.Steps import StartStep
from BlockSystem.BaseStep import BaseStep


class ChipProject(Project):
    def __init__(self):
        super().__init__()
        self._entityProcedureMapping: typing.Dict[ProjectEntity, 'ChipProject.Procedure'] = {}
        self._proceduresList: typing.List['ChipProject.Procedure'] = []
        self._currentProcedure: typing.Optional['ChipProject.Procedure'] = None
        self._valveBlocks: typing.List[ValveLogicBlock] = []

    def SetCurrentProcedure(self, procedure: 'ChipProject.Procedure'):
        self._currentProcedure = procedure

    def GetCurrentProcedure(self):
        return self._currentProcedure

    def StartProcedure(self):
        [block.Reset() for block in self.GetProjectBlocks() if isinstance(block, BaseStep)]
        
        if self._currentProcedure is not None:
            self._currentProcedure.Start()

    def StopProcedure(self):
        [block.Stop() for block in self.GetProjectBlocks() if isinstance(block, BaseStep)]

    def IsProcedureRunnable(self, procedure: 'ChipProject.Procedure'):
        return all(entity.GetBlock().IsValid() for entity in self.GetEntitiesInProcedure(procedure)
                   if isinstance(entity, BlockSystemEntity))

    def GetEntitiesInProcedure(self, procedure: 'ChipProject.Procedure'):
        return [entity for entity in self._entityProcedureMapping if self._entityProcedureMapping[entity] == procedure]

    def AddEntity(self, entity):
        super().AddEntity(entity)
        self._entityProcedureMapping[entity] = self._currentProcedure
        if isinstance(entity, BlockSystemEntity):
            block = entity.GetBlock()
            if isinstance(block, ValveLogicBlock) and block not in self._valveBlocks:
                self._valveBlocks.append(block)

    def RemoveEntity(self, entity: ProjectEntity):
        super().RemoveEntity(entity)
        self._entityProcedureMapping.pop(entity, None)
        if isinstance(entity, BlockSystemEntity):
            block = entity.GetBlock()
            if isinstance(block, ValveLogicBlock) and block in self._valveBlocks:
                self._valveBlocks.remove(block)

    def AddProcedure(self, procedure: 'ChipProject.Procedure'):
        if procedure not in self._proceduresList:
            self._proceduresList.append(procedure)
        return procedure

    def RemoveProcedure(self, procedure: 'ChipProject.Procedure'):
        if procedure in self._proceduresList:
            self._proceduresList.remove(procedure)
        [self.RemoveEntity(entity) for entity in self.GetEntitiesInProcedure(procedure)]

    def SendToRig(self, rig: Rig):
        for valveBlock in self._valveBlocks:
            rig.SetSolenoidState(valveBlock.solenoidNumberInput.GetValue(), valveBlock.openInput.GetValue())
        rig.Flush()

    class Procedure:
        def __init__(self, startStep: 'StartStep'):
            self.name = "New Procedure"
            self._startStep = startStep

        def Start(self):
            self._startStep.Start()
