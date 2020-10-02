from LogicBlocks.LogicBlock import *


class ValveLogicBlock(LogicBlock):
    def GetName(self=None):
        if self is None or self.GetNickname() == "":
            return "Valve"
        else:
            return self.GetNickname()

    def __init__(self):
        super().__init__()
        self.openInput = self.AddInput("Is Open?", bool)
        self.solenoidNumberInput = self.AddInput("Solenoid Number", int, False)
        self.nicknameInput = self.AddInput("Nickname", str, False)
        self.nicknameInput.SetDefaultData("Valve")
        self.minimized = False

    def GetSolenoidNumber(self):
        return self.solenoidNumberInput.GetData()

    def IsOpen(self) -> bool:
        return self.openInput.GetData()

    def GetNickname(self):
        return self.nicknameInput.GetData()
