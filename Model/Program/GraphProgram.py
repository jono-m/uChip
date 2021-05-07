import typing

from Program import Program, ProgramInstanceState, ProgramChipInterface


class GraphProgram(Program):
    def __init__(self):
        super().__init__()
        self.name = "New Graph Program"

        self.blocks: typing.List[GraphBlock] = []
        self.startBlock = GraphBlock("Program Start")
        self.startBlock.completedPorts += [CompletedPort("Begin", self.startBlock)]
        self.stopBlock = GraphBlock("On Program Stop")
        self.stopBlock.completedPorts += [CompletedPort("Begin", self.stopBlock)]

    def GetBlocks(self):
        return self.blocks.copy()

    def OnStart(self, instance: 'GraphProgramInstanceState'):
        instance.activeSteps = [self.startBlock]
        self.UpdateGraph(instance)

    def OnTick(self, instance: 'GraphProgramInstanceState'):
        self.UpdateGraph(instance)

    def UpdateGraph(self, instance: 'GraphProgramInstanceState'):
        updatedLogicBlocks = []

        logicBlocksToUpdate = self.blocks.copy()
        while logicBlocksToUpdate:
            logicBlocksReadyForUpdate = [block for block in logicBlocksToUpdate if
                                         all([dependency in updatedLogicBlocks for dependency in
                                              block.GetLogicDependencies()])]
            [logicBlocksToUpdate.remove(logicBlockReadyForUpdate) for logicBlockReadyForUpdate in
             logicBlocksReadyForUpdate]
            [logicBlockReadyForUpdate.UpdateLogic(instance) for logicBlockReadyForUpdate in logicBlocksReadyForUpdate]

        updatedSteps = []
        while instance.activeSteps:
            stepsToExecute = [step for step in instance.activeSteps if step not in updatedSteps]
            if not stepsToExecute:
                break
            updatedSteps += stepsToExecute
            [step.UpdateStep(instance) for step in stepsToExecute]

        if instance.IsRunning() and not instance.activeSteps:
            instance.Stop()

    def OnStop(self, instance: 'GraphProgramInstanceState'):
        instance.activeSteps = [self.stopBlock]
        self.UpdateGraph(instance)

    def CreateInstance(self, chipInterface: 'ProgramChipInterface') -> 'ProgramInstanceState':
        return GraphProgramInstanceState(self, chipInterface)


class GraphProgramInstanceState(ProgramInstanceState):
    def __init__(self, program: GraphProgram, chipInterface: ProgramChipInterface):
        super().__init__(program, chipInterface)
        self.graphProgram = program
        self.portData: typing.Dict[Port, typing.Any] = {}
        self.activeSteps: typing.List[GraphBlock] = []

        self.SyncWithProgram()

    def SyncWithProgram(self):
        super().SyncWithProgram()

        oldPortData = self.portData

        self.portData = {}

        for block in self.graphProgram.GetBlocks():
            for inputPort in block.inputPorts:
                if inputPort in oldPortData:
                    self.portData[inputPort] = oldPortData[inputPort]
                else:
                    self.portData[inputPort] = inputPort.valueWhenNoOutputConnected
            for outputPort in block.outputPorts:
                if outputPort in oldPortData:
                    self.portData[outputPort] = oldPortData[outputPort]
                else:
                    self.portData[outputPort] = outputPort.initialValue


class GraphBlock:
    def __init__(self, name="Graph Block"):
        self.xPosition = 0
        self.yPosition = 0

        self.name = name

        self.inputPorts = []
        self.outputPorts = []

        self.beginPorts = []
        self.completedPorts = []

    def GetLogicDependencies(self) -> typing.List['GraphBlock']:
        return [inputPort.GetConnectedOutput().block for inputPort in self.inputPorts if
                inputPort.GetConnectedOutput()]

    def UpdateLogic(self, instance: GraphProgramInstanceState):
        outputData = self.ComputeOutputs(self.PackageInputs(instance), instance)
        for outputPort in outputData:
            instance.portData[outputPort] = outputData[outputPort]

    def PackageInputs(self, instance: GraphProgramInstanceState):
        inputData = {}
        for inputPort in self.inputPorts:
            if inputPort.connectedOutput:
                inputData[inputPort] = instance.portData[inputPort.connectedOutput]
            else:
                inputData[inputPort] = inputPort.valueWhenNoOutputConnected
        return inputData

    def ComputeOutputs(self, inputData: typing.Dict['InputPort', typing.Any], instance: ProgramInstanceState) \
            -> typing.Dict['OutputPort', typing.Any]:
        pass

    def UpdateStep(self, instance: GraphProgramInstanceState):
        completedPorts = self.ExecuteStep(self.PackageInputs(instance), instance)
        if completedPorts:
            instance.activeSteps += completedPorts
            instance.activeSteps.remove(self)

    def ExecuteStep(self, inputData: typing.Dict['InputPort', typing.Any], instance: ProgramInstanceState) \
            -> typing.Optional[typing.List['CompletedPort']]:
        return self.completedPorts[:1]


class Port:
    def __init__(self, name: str, block: GraphBlock):
        self.name = name
        self.block = block


class InputPort(Port):
    def __init__(self, name: str, block: GraphBlock, dataType: typing.Type):
        super().__init__(name, block)
        self.dataType = dataType
        self.valueWhenNoOutputConnected = dataType()
        self.connectedOutput: typing.Optional[OutputPort] = None


class OutputPort(Port):
    def __init__(self, name: str, block: GraphBlock, dataType: typing.Type, initialValue):
        super().__init__(name, block)
        self.block = block
        self.dataType = dataType
        self.initialValue = initialValue


class BeginPort(Port):
    pass


class CompletedPort(Port):
    def __init__(self, name: str, block: GraphBlock):
        super().__init__(name, block)

        self.connectedBeginPorts: typing.List[BeginPort] = []
