from BaseStep import BaseStep
from Steps import StartStep
from BlockSystem.CompoundLogicBlock import CompoundLogicBlock
import typing


class Procedure(CompoundLogicBlock):
    def __init__(self):
        super().__init__()

        self.isRunning = False
        self.activeSteps: typing.List[BaseStep] = []
        self.startStep = StartStep()
        self.AddSubBlock(self.startStep)

    def GetSteps(self):
        return [x for x in self.GetSubBlocks() if isinstance(x, BaseStep)]

    def Start(self):
        for step in self.GetSteps():
            step.OnProcedureBegan()

        self.activeSteps.append(self.startStep)
        self.startStep.OnStepBegan()
        self.isRunning = True

    def Update(self):
        super().Update()
        for step in self.activeSteps.copy():
            if not step.isRunning:
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

        self.procedure = procedure

    def OnStepBegan(self):
        super().OnStepBegan()
        self.procedure.Start()

    def UpdateRunning(self):
        super().UpdateRunning()
        self.procedure.Update()

        if self.procedure.isRunning:
            self.progress = max(0.0, min(0.9999, self.procedure.activeSteps[0].GetProgress()))
        else:
            self.progress = 1

    def OnProcedureStopped(self):
        self.procedure.Stop()
