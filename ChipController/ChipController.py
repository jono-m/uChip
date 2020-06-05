from ChipController.ValveBlock import *
from Rig.Rig import Rig
from Procedures.Procedure import *
from LogicBlocks.CompoundLogicBlock import *


class ChipController:
    def __init__(self):
        self._filename = None

        self._logicBlock = CompoundLogicBlock()

        self._procedures: typing.List[Procedure] = []

        self.OnModified = Event()
        self.OnProcedureAdded = Event()
        self.OnProcedureRemoved = Event()
        self.OnSaved = Event()
        self.OnDestroyed = Event()

        self._logicBlock.OnModified.Register(self.OnModified.Invoke)
        self._logicBlock.OnBlockAdded.Register(self.OnBlockAdded)
        self._logicBlock.OnBlockRemoved.Register(self.OnBlockAdded)

        self.valveBlocks: typing.List[ValveLogicBlock] = []

        self.AddProcedure(Procedure())

    def Destroy(self):
        self._logicBlock.OnModified.Unregister(self.OnModified.Invoke)
        self._logicBlock.OnBlockAdded.Unregister(self.OnBlockAdded)
        self._logicBlock.OnBlockRemoved.Unregister(self.OnBlockAdded)
        self._logicBlock.Destroy()
        for procedure in self._procedures:
            procedure.Destroy()
        self.OnDestroyed.Invoke(self)

    def GetLogicBlock(self):
        return self._logicBlock

    def GetProcedures(self):
        return self._procedures.copy()

    def AddProcedure(self, procedure: 'Procedure'):
        self._procedures.append(procedure)
        procedure.OnModified.Register(self.OnModified.Invoke)
        procedure.OnDestroyed.Register(self.RemoveProcedure)
        self.OnModified.Invoke()
        self.OnProcedureAdded.Invoke(procedure)

    def RemoveProcedure(self, procedure: 'Procedure'):
        if procedure not in self._procedures:
            return
        self._procedures.remove(procedure)
        procedure.OnModified.Unregister(self.OnModified.Invoke)
        procedure.OnDestroyed.Unregister(self.RemoveProcedure)
        self.OnModified.Invoke()
        self.OnProcedureRemoved.Invoke(procedure)

    def GetFilename(self):
        return self._filename

    def OnBlockAdded(self, newBlock):
        if isinstance(newBlock, ValveLogicBlock):
            self.valveBlocks.append(newBlock)

    def OnBlockRemoved(self, block):
        if isinstance(block, ValveLogicBlock):
            self.valveBlocks.remove(block)

    def SendToRig(self, rig: Rig):
        rig.drivenSolenoids = []
        for valveBlock in self.valveBlocks:
            rig.SetSolenoid(int(valveBlock.GetSolenoidNumber()), valveBlock.IsOpen())
            rig.drivenSolenoids.append(valveBlock.GetSolenoidNumber())
        rig.Flush()

    def Save(self, filename=None):
        if filename is not None:
            self._filename = filename
        file = open(self._filename, "wb")
        pickle.dump(self, file)
        file.close()
        self.OnSaved.Invoke()

    @staticmethod
    def LoadFromFile(filename) -> typing.Optional['ChipController']:
        if not os.path.exists(filename):
            return None
        file = open(filename, "rb")
        chipController: ChipController = pickle.load(file)
        file.close()
        chipController._logicBlock.ReloadFileSubBlocks()
        return chipController

    def GetName(self):
        if self._filename is None:
            return "New Chip"
        else:
            name, extension = os.path.splitext(os.path.basename(self._filename))
            return name

