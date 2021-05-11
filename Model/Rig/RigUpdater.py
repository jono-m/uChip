from Model.Chip import Chip
from Model.Rig import Rig
from Model.Valve import ValveState


class RigUpdater:
    def __init__(self, rig: Rig, chip: Chip):
        self.chip = chip
        self.rig = rig

    def Tick(self):
        for valve in self.chip.valves:
            self.rig.SetSolenoidState(valve.solenoidNumber, valve.state is ValveState.OPEN)
