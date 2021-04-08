from LogicBlocks import BaseLogicBlock


class ValveLogicBlock(BaseLogicBlock):
    def GetName(self):
        if self.nicknameParameter.GetValue() == "":
            return "Valve " + self.solenoidNumberInput.GetValue()
        else:
            return self.nicknameParameter.GetValue()

    def __init__(self):
        super().__init__()
        self.nicknameParameter = self.CreateParameter("Nickname", str, "")
        self.openInput = self.CreateInputPort("Is Open?", bool)
        self.solenoidNumberInput = self.CreateParameter("Solenoid Number", int, 0)
