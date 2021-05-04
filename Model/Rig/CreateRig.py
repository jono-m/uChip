from Rig import Rig
from ElexolSerialDevice import ElexolSerialDevice

classesToTry = [ElexolSerialDevice]


def CreateRig():
    return Rig(classesToTry)
