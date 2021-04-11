from RigSystem.Rig import Rig
from RigSystem.ElexolSerialDevice import ElexolSerialDevice

classesToTry = [ElexolSerialDevice]


def CreateRig():
    return Rig(classesToTry)
