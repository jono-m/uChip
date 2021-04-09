import time
from BaseStep import BaseStep
from BlockSystem.Data import Data
from ProjectSystem import ChipProject
from BlockSystem.DataPorts import InputPort
import typing


class ChipSettingStep(BaseStep):
    def __init__(self, chipProject: ChipProject):
        super().__init__()

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


class WaitStep(BaseStep):
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


class StartStep(BaseStep):
    def GetName(self):
        return "Start"

    def __init__(self):
        super().__init__()
        self.AddCompletedPort("Start")


class IfStep(BaseStep):
    def GetName(self=None):
        return "Decision"

    def __init__(self):
        super().__init__()
        self.AddBeginPort()

        self.yesPort = self.AddCompletedPort("Yes")
        self.noPort = self.AddCompletedPort("No")
        self.conditionInput = self.AddPort(InputPort(Data("Condition", bool)))

    def GetNextPorts(self) -> typing.List['BaseStep.BeginPort']:
        if self.conditionInput.GetValue():
            return self.yesPort.GetConnectedPorts()
        else:
            return self.noPort.GetConnectedPorts()
