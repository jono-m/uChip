from UI.BaseEditorFrame import *
from UI.Chip.ChipEditor import *
from UI.Chip.ChipParametersList import *
from UI.Chip.ChipValvesList import *


class ChipEditorFrame(BaseEditorFrame):
    def __init__(self, rig: Rig):
        super().__init__()

        self.hLayout = QHBoxLayout()
        self.hLayout.setContentsMargins(0, 0, 0, 0)
        self.hLayout.setSpacing(0)
        self.setLayout(self.hLayout)

        self.chipController: typing.Optional[ChipController] = None

        self.editor = ChipEditor()
        self.nameFilters = "μChip Chip Controller (*.ucc)"

        self.hLayout.addWidget(self.editor, stretch=1)

        self.rig = rig

    def OpenChipController(self, chipController: ChipController):
        self.CloseChipController()
        self.chipController = chipController

        self.chipController.OnModified.Register(self.FileModified, True)
        self.chipController.OnSaved.Register(self.FileSaved, True)

        self.editor.LoadChipController(self.chipController)

        self.hasFilename = chipController.GetFilename() is not None

    def AddLogicBlock(self, lb: LogicBlock):
        lb.SetPosition(self.editor.worldBrowser.GetCenterPoint())
        self.chipController.GetLogicBlock().AddSubBlock(lb)

    def AddImage(self, image: Image):
        self.chipController.GetLogicBlock().AddImage(image)

    def GetName(self) -> str:
        return self.chipController.GetName()

    def CloseChipController(self):
        if self.chipController is not None:
            self.chipController.OnModified.Unregister(self.FileModified)
            self.chipController.OnSaved.Unregister(self.FileSaved)
            self.chipController.Close()
        self.editor.Clear()
        self.chipController = None

    def RequestClose(self):
        if super().RequestClose():
            self.CloseChipController()
            return True
        return False

    def RequestNew(self):
        if self.RequestClose():
            self.OpenChip(ChipController())

    def DoSave(self, filename=None):
        self.chipController.Save(filename)

    def UpdateFromSave(self):
        self.chipController.GetLogicBlock().ReloadFileSubBlocks()