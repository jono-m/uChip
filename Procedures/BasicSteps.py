import time
from Procedures.Step import *
from LogicBlocks.IOBlocks import *
from ChipController.ValveBlock import *


class ChipSettingStep(Step):
    def GetName(self=None):
        return "Set"

    def __init__(self, chipInputPort: InputPort):
        super().__init__()
        self.AddBeginPort()
        self.AddCompletedPort()

        self.valueInput = self.AddInput(chipInputPort.name, chipInputPort.dataType)
        self.chipInputPort = chipInputPort

        self.chipInputPort.block.OnPortsChanged.Register(self.Ensure)

    def UpdateOutputs(self):
        if self.valueInput.name != self.chipInputPort.name:
            self.valueInput.name = self.chipInputPort.name
            self.OnPortsChanged.Invoke(self)
        super().UpdateOutputs()

    def Ensure(self):
        if self.chipInputPort not in self.chipInputPort.block.GetInputs():
            self.chipInputPort.block.OnPortsChanged.Unregister(self.Ensure)
            super().Destroy()

    def Duplicate(self) -> 'LogicBlock':
        newB = ChipSettingStep(self.chipInputPort)
        self.OnDuplicated.Invoke(newB)
        return newB

    def BeginStep(self):
        self.chipInputPort.SetDefaultData(self.valueInput.GetData())
        super().BeginStep()


class ValveSettingStep(Step):
    def GetName(self=None):
        return "Set"

    def __init__(self, valveBlock: ValveLogicBlock):
        super().__init__()
        self.AddBeginPort()
        self.AddCompletedPort()

        self.valveBlock = valveBlock
        self.valueInput = self.AddInput("", valveBlock.openInput.dataType)

        self.valveBlock.OnConnectionsChanged.Register(self.Ensure)
        self.valveBlock.OnDestroyed.Register(self.Destroy)

    def Destroy(self):
        super().Destroy()
        self.valveBlock.OnDestroyed.Unregister(self.Destroy)
        self.valveBlock.OnConnectionsChanged.Unregister(self.Ensure)

    def Ensure(self):
        if self.valveBlock.openInput.connectedOutput is not None:
            self.Destroy()

    def UpdateOutputs(self):
        newName = self.valveBlock.GetName() + " Is Open?"
        if self.valueInput.name != newName:
            self.valueInput.name = newName
            self.OnPortsChanged.Invoke(self)
        super().UpdateOutputs()

    def Duplicate(self) -> 'LogicBlock':
        newB = ValveSettingStep(self.valveBlock)
        self.OnDuplicated.Invoke(newB)
        return newB

    def BeginStep(self):
        self.valveBlock.openInput.SetDefaultData(self.valueInput.GetData())
        super().BeginStep()


class CurrentSettingBlock(LogicBlock):
    def GetName(self=None):
        return "Current"

    def __init__(self, chipInputPort: InputPort):
        super().__init__()
        self.outputFromChip = self.AddOutput(chipInputPort.name, chipInputPort.dataType)
        self.chipInputPort = chipInputPort
        self.chipInputPort.block.OnPortsChanged.Register(self.Ensure)

    def Ensure(self):
        if self.chipInputPort not in self.chipInputPort.block.GetInputs():
            self.chipInputPort.block.OnPortsChanged.Unregister(self.Ensure)
            super().Destroy()

    def UpdateOutputs(self):
        if self.outputFromChip.name != self.chipInputPort.name:
            self.outputFromChip.name = self.chipInputPort.name
            self.OnPortsChanged.Invoke(self)
        self.outputFromChip.SetData(self.chipInputPort.GetData())
        super().UpdateOutputs()

    def Duplicate(self) -> 'LogicBlock':
        newB = CurrentSettingBlock(self.chipInputPort)
        self.OnDuplicated.Invoke(newB)
        return newB


class CurrentValveBlock(LogicBlock):
    def GetName(self=None):
        return "Current"

    def __init__(self, valveBlock: ValveLogicBlock):
        super().__init__()
        self.valveBlock = valveBlock
        self.outputFromChip = self.AddOutput("", valveBlock.openInput.dataType)
        self.valveBlock.OnConnectionsChanged.Register(self.Ensure)
        self.valveBlock.OnDestroyed.Register(self.Destroy)

    def Destroy(self):
        super().Destroy()
        self.valveBlock.OnDestroyed.Unregister(self.Destroy)
        self.valveBlock.OnConnectionsChanged.Unregister(self.Ensure)

    def Ensure(self):
        if self.valveBlock.openInput.connectedOutput is not None:
            self.Destroy()

    def UpdateOutputs(self):
        newName = self.valveBlock.GetName() + " Is Open?"
        if self.outputFromChip.name != newName:
            self.outputFromChip.name = newName
            self.OnPortsChanged.Invoke(self)
        self.outputFromChip.SetData(self.valveBlock.openInput.GetData())
        super().UpdateOutputs()

    def Duplicate(self) -> 'LogicBlock':
        newB = CurrentValveBlock(self.valveBlock)
        self.OnDuplicated.Invoke(newB)
        return newB


class WaitStep(Step):
    def GetName(self=None):
        return "Wait"

    def __init__(self):
        super().__init__()
        self.AddBeginPort()
        self.AddCompletedPort()
        self.startTime = None
        self.timeInput = self.AddInput("Time (s)", float)
        self.timeInput.SetDefaultData(1)

    def BeginStep(self):
        self.startTime = time.time()
        super().BeginStep()

    def UpdateStep(self) -> bool:
        super().UpdateStep()
        if time.time() - self.startTime >= self.timeInput.GetData():
            return True
        return False

    def GetProgress(self):
        if not self.IsRunning():
            return super().GetProgress()
        return (time.time() - self.startTime) / self.timeInput.GetData()


class StartStep(Step):
    def GetName(self=None):
        return "Start"

    def __init__(self):
        super().__init__()
        self.AddCompletedPort("Start")


class IfStep(Step):
    def GetName(self=None):
        return "Decision"

    def __init__(self):
        super().__init__()
        self.AddBeginPort()

        self.yesPort = self.AddCompletedPort("Yes")
        self.noPort = self.AddCompletedPort("No")
        self.conditionInput = self.AddInput("Condition", bool)

    def GetNextSteps(self) -> typing.List[Step]:
        if self.conditionInput.GetData():
            return self.yesPort.GetSteps()
        else:
            return self.noPort.GetSteps()
