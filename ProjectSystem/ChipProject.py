import typing

from ProjectSystem.Project import Project
from ProjectSystem.ProjectEntity import ProjectEntity
from ProjectSystem.BlockSystemEntity import BlockSystemEntity
from BlockSystem.Procedure import Procedure, ProcedureStep
from BlockSystem.LogicBlocks import ValveLogicBlock
from RigSystem.Rig import Rig


class ChipProject(Project):
    def __init__(self):
        super().__init__()
        self._entityProcedureMapping: typing.Dict[ProjectEntity, Procedure] = {}
        self._proceduresList: typing.List[Procedure] = []
        self._currentProcedure: typing.Optional[Procedure] = None

    def SetCurrentProcedure(self, procedure: Procedure):
        self._currentProcedure = procedure

    def GetCurrentProcedure(self):
        return self._currentProcedure

    def IsProcedureRunnable(self, procedure: Procedure):
        return all(entity.GetBlock().IsValid() for entity in self._entityProcedureMapping if
                   self._entityProcedureMapping[entity] == procedure and isinstance(entity, BlockSystemEntity))

    def GetEntitiesInProcedure(self, procedure: Procedure):
        return []

    def GetValveBlocks(self):
        return [block for block in self.GetProjectBlocks() if isinstance(block, ValveLogicBlock)]

    def AddEntity(self, entity):
        super().AddEntity(entity)
        self._entityProcedureMapping[entity] = self._currentProcedure

    def RemoveEntity(self, entity: ProjectEntity):
        super().RemoveEntity(entity)
        self._entityProcedureMapping.pop(entity, None)

    def AddProcedure(self, procedure: Procedure):
        if procedure not in self._proceduresList:
            self._proceduresList.append(procedure)
        return procedure

    def RemoveProcedure(self, procedure: Procedure):
        if procedure in self._proceduresList:
            self._proceduresList.remove(procedure)
        for entity in self._entityProcedureMapping.copy():
            if self._entityProcedureMapping[entity] == procedure:
                self.RemoveEntity(entity)
            if isinstance(entity, BlockSystemEntity):
                block = entity.GetBlock()
                if isinstance(block, ProcedureStep) and block.GetProcedure() == procedure:
                    block.SetInvalid("Procedure no longer exists.")

    def SendToRig(self, rig: Rig):
        for valveBlock in self.GetValveBlocks():
            rig.SetSolenoidState(valveBlock.solenoidNumberInput.GetValue(), valveBlock.openInput.GetValue())
        rig.Flush()
