from Data.Rig import Rig
from Data.FileIO import LoadObject
from pathlib import Path
import time

rig = Rig()
rig.allDevices = []
try:
    rig.allDevices = LoadObject(Path("devices.pkl"))
except EOFError:
    pass
except IOError:
    pass

rig.RescanForDevices()

t = False
while True:
    rig.SetSolenoidState(15, t)
    t = not t
    rig.FlushStates()
    time.sleep(0.05)