from ProjectSystem.Project import Project
from BlockSystem.BaseConnectableBlock import Parameter
from BlockSystem.BaseLogicBlock import BaseLogicBlock, InputPort, OutputPort
from ProjectSystem.BlockSystemEntity import BlockSystemEntity
from BlockSystem.Util import DatatypeToName, SyncParameters, SyncPorts
import typing


# A logic block that basically just executes any logic block entities that are actively in a project.
# Used for running a chip project, testing out a logic block project,
# or for executing a custom logic block in another project.
class ProjectLogicBlock(BaseLogicBlock):
    def GetName(self):
        if not self.IsValid():
            return "Invalid Project Block"
        return self._project.GetProjectName()

    def __init__(self):
        super().__init__()
        self._project: typing.Optional[Project] = None

        self.parameterMapping: typing.Dict[Parameter, InputLogicBlock] = {}
        self.inputMapping: typing.Dict[InputPort, InputLogicBlock] = {}
        self.outputMapping: typing.Dict[OutputPort, OutputLogicBlock] = {}

    def IsValid(self):
        return self._project is not None and all([block.IsValid() for block in self.GetSubBlocks()])

    def LoadProject(self, project: Project):
        self._project = project

    def GetSubBlocks(self):
        return [entity.GetBlock() for entity in self._project.GetEntities() if isinstance(entity, BlockSystemEntity)]

    def PushCurrentParametersAndInputs(self):
        for inputPort in self.GetInputPorts():
            self.inputMapping[inputPort].defaultValueParameter.SetValue(inputPort.GetValue())

        for parameter in self.GetParameters():
            self.parameterMapping[parameter].defaultValueParameter.SetValue(parameter.GetValue())

    def PullCurrentOutputs(self):
        for outputPort in self.GetOutputPorts():
            outputPort.SetValue(self.outputMapping[outputPort].input.GetValue())

    def Sync(self):
        subBlocks = self.GetSubBlocks()
        parameterBlocks = [entity for entity in subBlocks if isinstance(entity, InputLogicBlock) and entity.isParameter]
        inputBlocks = [entity for entity in subBlocks if isinstance(entity, InputLogicBlock) and not entity.isParameter]
        outputBlocks = [entity for entity in subBlocks if isinstance(entity, OutputLogicBlock)]

        SyncParameters(self, {key: value for (key, value) in
                              [(parameterBlock.nameParameter.GetValue(),
                                (parameterBlock.dataType, parameterBlock.defaultValueParameter.GetValue()))
                               for parameterBlock in parameterBlocks]})
        SyncPorts(self,
                  {key: value for (key, value) in
                   [(inputBlock.nameParameter.GetValue(),
                     (inputBlock.dataType, inputBlock.defaultValueParameter.GetValue()))
                    for inputBlock in inputBlocks]},
                  {key: value for (key, value) in
                   [(outputBlock.nameParameter.GetValue(), outputBlock.dataType)
                    for outputBlock in outputBlocks]})

    def Update(self):
        super().Update()

        if not self.IsValid():
            return

        self.PushCurrentParametersAndInputs()
        self.UpdateSubBlocks()
        self.PullCurrentOutputs()

    def UpdateSubBlocks(self):
        blocksWaitingForUpdate = self.GetSubBlocks()
        while blocksWaitingForUpdate:
            blocksReadyForUpdate = []
            for blockWaitingForUpdate in blocksWaitingForUpdate:
                if isinstance(blockWaitingForUpdate, BaseLogicBlock):
                    parentBlocks = [port.ownerBlock for port in blockWaitingForUpdate.GetInputPorts()]
                    areAllParentsUpdated = all(
                        parentBlock not in blocksWaitingForUpdate for parentBlock in parentBlocks)
                else:
                    areAllParentsUpdated = True
                if areAllParentsUpdated:
                    blocksReadyForUpdate.append(blockWaitingForUpdate)

            for blockReadyForUpdate in blocksReadyForUpdate:
                blocksWaitingForUpdate.remove(blockReadyForUpdate)
                blockReadyForUpdate.Update()


# Dummy logic block that represents an input to the project logic block
class InputLogicBlock(BaseLogicBlock):
    def __init__(self, dataType):
        super().__init__()
        self.dataType = dataType

        self.nameParameter = self.CreateParameter("Name", str, "New" + DatatypeToName(self.dataType))
        self.defaultValueParameter = self.CreateParameter("Initial Value", dataType)
        self.isParameter = self.CreateParameter("Is Parameter", bool, False)
        self.output = self.CreateOutputPort("Value", self.dataType)

    def GetName(self):
        return self.nameParameter.GetValue()

    def Update(self):
        super().Update()
        self.output.SetValue(self.defaultValueParameter)


class OutputLogicBlock(BaseLogicBlock):
    def __init__(self, dataType):
        super().__init__()
        self.dataType = dataType

        self.nameParameter = self.CreateParameter("Name", str, "New" + DatatypeToName(self.dataType))
        self.input = self.CreateInputPort("Value", self.dataType)
