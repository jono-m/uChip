import time
from BaseStep import BaseStep, BeginPort
from BlockSystem.BaseLogicBlock import BaseLogicBlock, InputPort, OutputPort
from BlockSystem.ValveLogicBlock import ValveLogicBlock
import typing


class ChipSettingStep(BaseStep):
    def GetName(self):
        return "Set Chip Parameter: " + self.chipInputPort.name

    def __init__(self, chipInputPort: InputPort):
        super().__init__()

        self.CreateBeginPort()
        self.CreateCompletedPort()

        self.valueInput = self.CreateInputPort(chipInputPort.name, chipInputPort.dataType)

        self._initialValue = None

        self.chipInputPort = chipInputPort

    def Update(self):
        super().Update()
        self.valueInput.name = self.chipInputPort.name
        if self.valueInput.dataType != self.chipInputPort.dataType:
            self.valueInput.dataType = self.chipInputPort.dataType
            self.valueInput.SetDefaultValue(self.chipInputPort.GetDefaultValue())

        # This is only valid if the chip input port actually exists
        self.isValid = self.chipInputPort.ownerBlock is not None

    def OnProcedureBegan(self):
        self._initialValue = self.chipInputPort.GetDefaultValue()

    def OnProcedureStopped(self):
        self.chipInputPort.SetDefaultValue(self._initialValue)

    def OnStepBegan(self):
        super().OnStepBegan()
        self.chipInputPort.SetDefaultValue(self.valueInput.GetValue())


class ValveSettingStep(BaseStep):
    def GetName(self):
        return "Set Valve: " + self.valveBlock.GetName()

    def __init__(self, valveBlock: ValveLogicBlock):
        super().__init__()
        self.CreateBeginPort()
        self.CreateCompletedPort()

        self.valveBlock = valveBlock
        self.valueInput = self.CreateInputPort("Is Open?", bool)

        self._initialValveState = False

    def Update(self):
        super().Update()
        self.isValid = self.valveBlock.isValid and self.valveBlock.openInput.GetConnectedOutput() is None

    def OnStepBegan(self):
        super().OnStepBegan()
        self.valveBlock.openInput.SetDefaultValue(self.valueInput.GetValue())

    def OnProcedureBegan(self):
        self._initialValveState = self.valveBlock.openInput.GetDefaultValue()

    def OnProcedureStopped(self):
        self.valveBlock.openInput.SetDefaultValue(self._initialValveState)


class CurrentValueBlock(BaseLogicBlock):
    def GetName(self):
        return "Current Value: " + self.chipPort.name

    def __init__(self, chipPort: typing.Union[InputPort, OutputPort]):
        super().__init__()
        self.valueFromChip = self.CreateOutputPort(chipPort.name, chipPort.dataType)
        self.chipPort = chipPort

    def Update(self):
        super().Update()
        self.valueFromChip.name = self.chipPort.name
        self.valueFromChip.SetValue(self.chipPort.GetValue())

        self.isValid = self.chipPort.ownerBlock is not None


class WaitStep(BaseStep):
    def GetName(self=None):
        return "Wait"

    def __init__(self):
        super().__init__()
        self.CreateBeginPort()
        self.CreateCompletedPort()

        self._startTime: typing.Optional[float] = None

        self.timeInput = self.CreateInputPort("Time (s)", float, 1)

    def OnStepBegan(self):
        super().OnStepBegan()
        self._startTime = time.time()

    def UpdateRunning(self):
        super().UpdateRunning()
        self.progress = (time.time() - self._startTime) / self.timeInput.GetValue()


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
        self.conditionInput = self.CreateInputPort("Condition", bool)

    def GetNextPorts(self) -> typing.List['BeginPort']:
        if self.conditionInput.GetValue():
            return self.yesPort.GetConnectedPorts()
        else:
            return self.noPort.GetConnectedPorts()
