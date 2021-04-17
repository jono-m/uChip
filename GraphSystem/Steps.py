import time
from BaseStep import ProcedureStep
from GraphSystem.Data import Data
from ProjectSystem import ChipProject
from GraphSystem.DataPorts import InputPort, OutputPort
import typing


class ChipSettingStep(ProcedureStep):
    def GetName(self):
        return "Set Chip Settings"

    def __init__(self, chipProject: ChipProject):
        super().__init__()

        self.AddBeginPort()
        self.AddCompletedPort()

        self._chipProject = chipProject
        self._settingsPairs: typing.List[(InputPort, Data)] = []

    def GetSettings(self):
        return self._settingsPairs

    def AddSetting(self, setting: Data):
        port = self.AddPort(InputPort(setting.Copy()))
        self._settingsPairs.append((port, setting))

    def Update(self):
        super().Update()
        for settingPair in self._settingsPairs.copy():
            (port, setting) = settingPair
            if setting not in self._chipProject.GetSettings():
                self.RemovePort(port)
                self._settingsPairs.remove(settingPair)
            else:
                port.SetName(setting.GetName())


class LoopStep(ProcedureStep):
    def GetName(self):
        if self.isRunning:
            return "Repeat (" + str(self._iterationsCompleted) + "/" + str(self.timesPort.GetName()) + " times)"
        else:
            return "Repeat (" + str(self.timesPort.GetName()) + " times)"

    def __init__(self):
        super().__init__()
        self._iterationsCompleted = 0
        self.AddBeginPort()
        self.repeatPort = self.AddCompletedPort("Repeat")
        self.completedPort = self.AddCompletedPort("Finished")
        self.timesPort = self.AddPort(InputPort(Data("Iterations", int)))
        self.iterationPort = self.AddPort(OutputPort(Data("Iterations Completed", int)))

        self._isLooping = False

    def OnStepBegan(self):
        super().OnStepBegan()
        if self._isLooping:
            self._iterationsCompleted += 1
        else:
            self._iterationsCompleted = 0
            self._isLooping = True

    def Update(self):
        super().Update()
        self.iterationPort.SetValue(self._iterationsCompleted)

    def OnStepCompleted(self):
        super().OnStepCompleted()
        if self._iterationsCompleted >= self.timesPort.GetValue():
            self._isLooping = False

    def GetNextPorts(self) -> typing.List['ProcedureStep.CompletedPort']:
        if self._iterationsCompleted >= self.timesPort.GetValue():
            return [self.completedPort]
        else:
            return [self.repeatPort]


class WaitStep(ProcedureStep):
    def GetName(self):
        return "Wait"

    def __init__(self):
        super().__init__()
        self.AddBeginPort()

        self.AddCompletedPort()

        self._startTime: typing.Optional[float] = None

        self.timeInput = self.AddPort(InputPort(Data("Time (s)", float, 1)))
        self.terminateEarly = self.AddPort(InputPort(Data("End Now", bool, False)))

    def OnStepBegan(self):
        super().OnStepBegan()
        self._startTime = time.time()

    def OnStepTick(self):
        super().Update()
        if self.terminateEarly.GetValue():
            self.SetProgress(1)
        else:
            self.SetProgress((time.time() - self._startTime) / self.timeInput.GetValue())


class IfStep(ProcedureStep):
    def GetName(self=None):
        return "Decision"

    def __init__(self):
        super().__init__()
        self.AddBeginPort()

        self.yesPort = self.AddCompletedPort("Yes")
        self.noPort = self.AddCompletedPort("No")
        self.conditionInput = self.AddPort(InputPort(Data("Condition", bool)))

    def GetNextPorts(self) -> typing.List['ProcedureStep.CompletedPort']:
        if self.conditionInput.GetValue():
            return self.yesPort
        else:
            return self.noPort


class StartStep(ProcedureStep):
    def GetName(self):
        return "Start of Procedure"

    def __init__(self):
        super().__init__()
        self.AddCompletedPort("Start")
