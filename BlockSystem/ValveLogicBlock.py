from LogicBlocks import BaseLogicBlock


class ValveLogicBlock(BaseLogicBlock):
    def GetName(self):
        if self.nicknameParameter.GetValue() == "":
            return "Valve " + self.solenoidNumber.GetValue()
        else:
            return self.nicknameParameter.GetValue()

    def __init__(self):
        super().__init__()
        self.nicknameParameter = self.CreateParameter("Nickname", str, "")
        self.openInput = self.CreateInputPort("Is Open?", bool)
        self.solenoidNumber = self.CreateParameter("Solenoid Number", int, 0)
