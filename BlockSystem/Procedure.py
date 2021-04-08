from BaseStep import BaseStep
from Steps import StartStep
import typing


class Procedure:
    def __init__(self, startStep: StartStep):
        super().__init__()

        self.isRunning = False
        self.activeSteps: typing.List[BaseStep] = []
        self.startStep = startStep

        self.name = "New Procedure"

    def Start(self):
        for step in self.GetSteps():
            step.OnProcedureBegan()

        self.activeSteps.append(self.startStep)
        self.startStep.OnStepBegan()
        self.isRunning = True

    def GetSteps(self):
        visitedSteps = []
        stepsToExpand = [self.startStep]
        while stepsToExpand:
            stepToExpand = stepsToExpand.pop(0)
            visitedSteps.append(stepToExpand)
            [stepsToExpand.append(port.ownerBlock) for port in stepToExpand.GetCompletedPorts() if
             port.ownerBlock not in visitedSteps]
        return visitedSteps

    def UpdateProcedure(self):
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
        self.procedure.UpdateProcedure()

        if self.procedure.isRunning:
            self.progress = max(0.0, min(0.9999, self.procedure.activeSteps[0].GetProgress()))
        else:
            self.progress = 1

    def OnProcedureStopped(self):
        self.procedure.Stop()
