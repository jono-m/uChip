from BaseStep import BaseStep
from BaseConnectableBlock import BaseConnectableBlock
from Steps import StartStep
import typing


class Procedure:
    def __init__(self, startStep: StartStep):
        super().__init__()

        self.isRunning = False
        self.activeSteps: typing.List[BaseStep] = []
        self.startStep = startStep

        self._blocks: typing.List[BaseConnectableBlock] = [startStep]

        self.name = "New Procedure"

    def Start(self):
        for step in self.GetSteps():
            step.OnProcedureBegan()

        self.activeSteps.append(self.startStep)
        self.startStep.OnStepBegan()
        self.isRunning = True

    def AddBlock(self, block: BaseConnectableBlock):
        if block not in self._blocks:
            self._blocks.append(block)

    def RemoveBlock(self, block: BaseConnectableBlock):
        if block in self._blocks:
            self._blocks.remove(block)

    def GetBlocks(self):
        return self._blocks

    def GetSteps(self):
        return [block for block in self.GetBlocks() if isinstance(block, BaseStep)]

    def UpdateProcedure(self):
        for step in self.activeSteps.copy():
            step.Update()
            if step._progress >= 1.0:
                step.OnStepCompleted()
                self.activeSteps.remove(step)
                for beginPort in step.GetNextPorts():
                    if isinstance(beginPort.ownerBlock, BaseStep):
                        beginPort.ownerBlock.OnStepBegan()
                        self.activeSteps.append(beginPort.ownerBlock)
        self.isRunning = len(self.activeSteps) > 0

    def Stop(self):
        for step in self.GetSteps():
            step.OnProcedureStopped()
        self.activeSteps = []
        self.isRunning = False


class ProcedureStep(BaseStep):
    def GetName(self):
        return "Procedure: " + self.procedure.name

    def __init__(self, procedure: Procedure):
        super().__init__()

        self.CreateBeginPort()
        self.CreateCompletedPort()
        self.procedure = procedure

    def OnStepBegan(self):
        super().OnStepBegan()
        self.procedure.Start()

    def Update(self):
        super().Update()
        self.procedure.UpdateProcedure()

        if self.procedure.isRunning:
            self.progress = max(0.0, min(0.9999, self.procedure.activeSteps[0].GetProgress()))
        else:
            self.progress = 1

    def OnProcedureStopped(self):
        self.procedure.Stop()
