from ProjectEntity import ProjectEntity
from BlockSystem.BaseStep import BaseStep
from BlockSystem.ProcedureStep import StartStep
import typing


class ProcedureRunner:
    def __init__(self, startStep: 'StartStep'):
        self.name = "New Procedure"
        self._startStep = startStep

        self._activeSteps: typing.List[StartStep] = []

        self._isRunning = False

    def IsRunning(self):
        return self._isRunning

    def Start(self):
        if self.IsRunning():
            self.Stop()
        self._isRunning = True
        self._activeSteps.append(self._startStep)

        for step in self._startStep.GetConnectedSteps():
            step.OnProcedureBegan()

        self._startStep.OnStepBegan()

    def Update(self):
        for step in self._activeSteps.copy():
            if step.IsCompleted():

        if len(self._activeSteps) == 0:
            self.Stop()

    def Stop(self):
        for step in self._startStep.GetConnectedSteps():
            step.OnProcedureStopped()
        self._isRunning = False
