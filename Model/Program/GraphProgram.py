from typing import Set, Dict, Type

from Parameter import Parameter
from Output import Output
from ProgramInstanceState import ProgramInstanceState, ProgramPhase
from Data import DataValueType
from Program import Program, ProgramChipInterface
from GraphBlock import GraphBlock, StepPort


class GraphProgramInstanceState(ProgramInstanceState):
    def __init__(self):
        super().__init__()
        self.blockInstances: Dict[GraphBlock, ProgramInstanceState] = {}

    def SyncBlocks(self, blocks: Set[GraphBlock]):
        self.blockInstances = {block: self.blockInstances[block] for block in self.blockInstances if block in blocks}

        for block in blocks:
            if block not in self.blockInstances:
                self.blockInstances[block] = block.CreateInstance()


class GraphProgram(Program):
    def __init__(self):
        super().__init__("New Graph Program")

        self._blocks: Set[GraphBlock] = set()
        self._dataConnections: Dict[Parameter, Output] = {}
        self._parameterValuesWhenNoOutput: Dict[Parameter, DataValueType] = {}
        self._stepConnections: Dict[StepPort, Set[StepPort]] = {}

        self._startBlock = PhaseBlock("On Started")
        self._pauseBlock = PhaseBlock("On Paused")
        self._resumeBlock = PhaseBlock("On Resumed")
        self._stoppedBlock = PhaseBlock("On Stopped")

        self._phaseBlocks = [self._startBlock, self._pauseBlock, self._resumeBlock, self._stoppedBlock]

    def ComputeOutputs(self, state: GraphProgramInstanceState, interface: 'ProgramChipInterface'):
        # TODO: Update the output tree.
        pass

    def OnStart(self, state: GraphProgramInstanceState, chipInterface: 'ProgramChipInterface'):
        self.ComputeOutputs(state, chipInterface)
        self.StartStep(self._startBlock, state, chipInterface, False)

    def OnPause(self, state: GraphProgramInstanceState, chipInterface: 'ProgramChipInterface'):
        self.ComputeOutputs(state, chipInterface)
        self.StartStep(self._pauseBlock, state, chipInterface, True)

    def OnResume(self, state: GraphProgramInstanceState, chipInterface: 'ProgramChipInterface'):
        self.ComputeOutputs(state, chipInterface)

    def OnTick(self, state: GraphProgramInstanceState, chipInterface: 'ProgramChipInterface'):
        self.ComputeOutputs(state, chipInterface)

    def OnStop(self, state: GraphProgramInstanceState, chipInterface: 'ProgramChipInterface'):
        self.ComputeOutputs(state, chipInterface)

    def StartStep(self, block: GraphBlock, state: GraphProgramInstanceState, interface: 'ProgramChipInterface',
                  oneShot):
        interface.StartProgram(block, state.blockInstances[block], state, oneShot,
                               lambda: self.OnStepCompleted(block, state, interface, oneShot))

    def OnStepCompleted(self, block: GraphBlock, state: GraphProgramInstanceState, interface: 'ProgramChipInterface',
                        oneShot: bool):
        nextPort = block.GetNextPort(state.blockInstances[block])
        if nextPort and nextPort in self._stepConnections:
            nextBlocks = [port.GetBlock() for port in self._stepConnections[nextPort]]
            [self.StartStep(block, state, interface, oneShot) for block in nextBlocks]

        if not interface.GetChildPrograms(state) and state.GetPhase() is ProgramPhase.RUNNING:
            interface.FinishProgram(state)

    def GetPhaseBlocks(self):
        return self._phaseBlocks

    def GetBlocks(self):
        return self._blocks

    def AddBlock(self, block: GraphBlock):
        if block in self._blocks:
            raise Exception("Block already added")
        self._blocks.add(block)

    def RemoveBlock(self, block: GraphBlock):
        if block not in self._blocks:
            raise Exception("Block was not in collection.")
        if block in self._phaseBlocks.values():
            raise Exception("Do not delete phase blocks!")
        self._blocks.remove(block)

    def GetDataConnections(self):
        return self._dataConnections

    def ConnectData(self, output: Output, parameter: Parameter):
        self._dataConnections[parameter] = output

    def DisconnectData(self, output: Output, parameter: Parameter):
        if parameter in self._dataConnections and self._dataConnections[parameter] == output:
            del self._dataConnections[parameter]
        else:
            raise Exception("Data were not connected.")

    def GetParameterValuesWhenNoOutput(self):
        return self._parameterValuesWhenNoOutput

    def SetParameterValueWhenNoOutput(self, parameter: Parameter, value: DataValueType):
        self._parameterValuesWhenNoOutput[parameter] = parameter.CastClamped(value)

    def ValidateParameterValuesWhenNoOutput(self):
        for parameter in self._parameterValuesWhenNoOutput:
            self._parameterValuesWhenNoOutput[parameter] = parameter.CastClamped(
                self._parameterValuesWhenNoOutput[parameter])

    def GetStepConnections(self):
        return self._stepConnections

    def ConnectSteps(self, portA: StepPort, portB: StepPort):
        if not portA.IsCompatible(portB):
            raise Exception("Ports are not compatible!")
        if portA.GetPortType() == StepPort.PortType.COMPLETED:
            completedPort = portA
            beginPort = portB
        else:
            completedPort = portB
            beginPort = portA

        if completedPort not in self._stepConnections:
            self._stepConnections[completedPort] = {beginPort}
        else:
            self._stepConnections[completedPort].add(beginPort)

    def DisconnectSteps(self, portA: StepPort, portB: StepPort):
        if portA.GetPortType() == StepPort.PortType.COMPLETED:
            completedPort = portA
            beginPort = portB
        else:
            completedPort = portB
            beginPort = portA

        if completedPort in self._stepConnections and beginPort in self._stepConnections[completedPort]:
            self._stepConnections[completedPort].remove(beginPort)
        else:
            raise Exception("Steps were not connected.")

    def GC(self):
        allParameters = sum([block.GetParameters() for block in self.GetBlocks()], [])
        allOutputs = sum([block.GetOutputs() for block in self.GetBlocks()], [])
        allCompletedPorts = sum([block.GetCompletedPorts() for block in self.GetBlocks()], [])
        allBeginPorts = sum([block.GetBeginPorts() for block in self.GetBlocks()], [])
        self._dataConnections = {parameter: self._dataConnections[parameter] for parameter in self._dataConnections
                                 if parameter in allParameters and self._dataConnections[parameter] in allOutputs}
        self._parameterValuesWhenNoOutput = {parameter: self._parameterValuesWhenNoOutput[parameter] for parameter in
                                             self._parameterValuesWhenNoOutput if parameter in allParameters}
        self._stepConnections = {stepPort: self._stepConnections[stepPort] for stepPort in self._stepConnections if
                                 stepPort in allCompletedPorts}

        for completedPort in self._stepConnections:
            self._stepConnections[completedPort] = [beginPort for beginPort in self._stepConnections[completedPort] if
                                                    beginPort in allBeginPorts]

    @staticmethod
    def GetStateType() -> Type[ProgramInstanceState]:
        return GraphProgramInstanceState

    def InitializeInstance(self, newInstance: GraphProgramInstanceState):
        super().InitializeInstance(newInstance)
        newInstance.SyncBlocks(self.GetBlocks())


class PhaseBlock(GraphBlock):
    def __init__(self, name: str):
        super().__init__(name)

        self.AddCompletedPort("Begin")
