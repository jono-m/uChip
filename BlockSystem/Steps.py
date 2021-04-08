import time
from BaseStep import BaseStep, BeginPort
from BlockSystem.BaseLogicBlock import InputPort, OutputPort, BaseLogicBlock
from BlockSystem.BaseConnectableBlock import Port
import typing


class ChipSettingStep(BaseStep):
    def GetName(self):
        return "Set Value"

    def __init__(self):
        super().__init__()

        self.CreateBeginPort()
        self.CreateCompletedPort()

        self.valueInput = InputPort("Value", None)
        self.AddPort(self.valueInput)
        self.valueOutput = SettingPort("Set", None)
        self.AddPort(self.valueOutput)

        self._initialValue = None

    def OnProcedureBegan(self):
        super().OnProcedureBegan()
        self._initialValue = self.valueInput.GetValue()

    def OnProcedureStopped(self):
        super().OnProcedureStopped()
        for inputPort in self.valueOutput.GetConnectedPorts():
            if isinstance(inputPort, InputPort):
                inputPort.SetDefaultValue(self._initialValue)

    def OnStepBegan(self):
        super().OnStepBegan()
        for inputPort in self.valueOutput.GetConnectedPorts():
            if isinstance(inputPort.ownerBlock, ChipSettingBlock):
                inputPort.ownerBlock.Set(self.valueInput.GetValue())


class ChipSettingBlock(BaseLogicBlock):
    def GetName(self) -> str:
        return "Chip Parameter:\n" + str(self._chipInputPort.name)

    def __init__(self, chipInputPort: InputPort):
        super().__init__()
        self._chipInputPort = chipInputPort

        self.settingPort = self.CreateInputPort("Set", self._chipInputPort.dataType,
                                                self._chipInputPort.GetDefaultValue())
        self.currentValuePort = self.CreateOutputPort("Current", self._chipInputPort.dataType)

    def Update(self):
        super().Update()
        if self._chipInputPort.ownerBlock is None:
            self.SetInvalid("Setting no longer exists.")
        else:
            self.SetValid()

        self.settingPort.dataType = self._chipInputPort.dataType
        self.currentValuePort.dataType = self._chipInputPort.dataType
        self.currentValuePort.SetValue(self._chipInputPort.GetValue())

    def Set(self, value):
        self._chipInputPort.SetDefaultValue(value)


class SettingPort(OutputPort):
    def CanConnect(self, port: 'Port'):
        if not super().CanConnect(port):
            return False
        return isinstance(port.ownerBlock, ChipSettingBlock)


class WaitStep(BaseStep):
    def GetName(self=None):
        return "Wait"

    def __init__(self):
        super().__init__()
        self.CreateBeginPort()
        self.CreateCompletedPort()

        self._startTime: typing.Optional[float] = None

        self.timeInput = InputPort("Time (s)", float, 1)
        self.AddPort(self.timeInput)

        self.terminateEarly = InputPort("End Now", bool, False)
        self.AddPort(self.terminateEarly)

        self._waitTime = 1

    def OnStepBegan(self):
        super().OnStepBegan()
        self._startTime = time.time()
        self._waitTime = self.timeInput.GetValue()

    def Update(self):
        super().Update()
        if self.terminateEarly.GetValue():
            self.progress = 1
        else:
            self.progress = (time.time() - self._startTime) / self._waitTime


class StartStep(BaseStep):
    def GetName(self=None):
        return "Start"

    def __init__(self):
        super().__init__()
        self.CreateCompletedPort("Start")


class IfStep(BaseStep):
    def GetName(self=None):
        return "Decision"

    def __init__(self):
        super().__init__()
        self.CreateBeginPort()

        self.yesPort = self.CreateCompletedPort("Yes")
        self.noPort = self.CreateCompletedPort("No")
        self.conditionInput = InputPort("Condition", bool)
        self.AddPort(self.conditionInput)

    def GetNextPorts(self) -> typing.List['BeginPort']:
        if self.conditionInput.GetValue():
            return self.yesPort.GetConnectedPorts()
        else:
            return self.noPort.GetConnectedPorts()
