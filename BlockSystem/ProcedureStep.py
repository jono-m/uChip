from BlockSystem.BaseStep import BaseStep
from ProjectSystem.Procedure import ProcedureEntity
import typing


class ProcedureStep(BaseStep):
    def __init__(self, procedure: ProcedureEntity):
        super().__init__()
        self._procedure = procedure

        self.AddBeginPort()
        self.AddCompletedPort()

    def GetProcedure(self):
        return self._procedure

    def GetName(self):
        return self._procedure.name + " (procedure)"

    def OnStepBegan(self):
        super().OnStepBegan()
        self._procedure.Start()

    def GetProgress(self):
        if self._procedure.IsRunning():
            return 0.0
        else:
            return 1.0


class StartStep(BaseStep):
    def GetName(self):
        return "Start of Procedure"

    def __init__(self):
        super().__init__()
        self.AddCompletedPort("Start")

    def GetConnectedSteps(self):
        visitedSteps: typing.List[BaseStep] = []

        stepsToVisit = [self]

        while stepsToVisit:
            stepToVisit = stepsToVisit.pop(0)
            visitedSteps.append(stepToVisit)
            for completedPort in stepToVisit.GetPorts(BaseStep.CompletedPort):
                for beginPort in completedPort.GetConnectedPorts():
                    if isinstance(beginPort, BaseStep.BeginPort) and beginPort.GetOwnerBlock() not in visitedSteps:
                        visitedSteps.append(beginPort.GetOwnerBlock())

        return visitedSteps
