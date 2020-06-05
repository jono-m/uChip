from Procedures.BasicSteps import *
from LogicBlocks.CompoundLogicBlock import *


class Procedure(CompoundLogicBlock):
    def GetName(self=None):
        if self is None:
            return "Procedure"
        else:
            return self._name

    def __init__(self):
        super().__init__()
        self._name = "New Procedure"
        self._currentActiveSteps: typing.List[Step] = []
        self._firstStep = StartStep()
        self.AddSubBlock(self._firstStep)
        self.OnNameChanged = Event()

        self.initialData: typing.Dict[InputPort, typing.Any] = {}

    def GetSteps(self):
        return [x for x in self.GetSubBlocks() if isinstance(x, Step)]

    def SetName(self, newName: str):
        self._name = newName
        self.OnNameChanged.Invoke(newName)

    def Start(self):
        for step in self.GetSteps():
            step.BeginProcedure()

        self._currentActiveSteps.append(self._firstStep)
        self._firstStep.BeginStep()

        self.initialData = {}

        settingSteps = [settingStep for settingStep in self.GetSubBlocks() if isinstance(settingStep, ChipSettingStep)]
        for settingStep in settingSteps:
            if settingStep.chipInputPort not in self.initialData:
                self.initialData[settingStep.chipInputPort] = settingStep.chipInputPort.GetData()

    def Stop(self):
        for step in self.GetSteps():
            step.StopProcedure()

        for inputPort in self.initialData:
            inputPort.SetDefaultData(self.initialData[inputPort])
        self.initialData = {}

    def Update(self) -> bool:
        self.UpdateOutputs()
        for step in self._currentActiveSteps[:]:
            if step.UpdateStep():
                step.FinishStep()
                self._currentActiveSteps.remove(step)
                nextSteps = step.GetNextSteps()
                for nextStep in nextSteps:
                    nextStep.BeginStep()
                    self._currentActiveSteps.append(nextStep)

        if len(self._currentActiveSteps) == 0:
            self.Stop()
            return True
        return False
