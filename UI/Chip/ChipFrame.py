from UI.FileViewerFrame import *
from PySide2.QtCore import *
from UI.Chip.ChipEditor import *
from UI.Chip.ChipParametersList import *
from UI.Chip.ChipValvesList import *


class ChipFrame(FileViewerFrame):
    def __init__(self, rig: Rig):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.chipController: typing.Optional[ChipController] = None

        self.chipEditor = ChipEditor()

        vLayout = QVBoxLayout()
        self.chipParametersList = ChipParametersList()
        vLayout.addWidget(self.chipParametersList)
        self.valvesList = ChipValvesList()
        vLayout.addWidget(self.valvesList)

        layout.addLayout(vLayout)
        layout.addWidget(self.chipEditor, stretch=1)

        self.rig = rig

    def SetIsProcedureRunning(self, running):
        self.chipEditor.worldBrowser.actionsEnabled = not running
        self.chipEditor.worldBrowser.update()
        self.chipParametersList.setEnabled(not running)
        self.valvesList.setEnabled(not running)

    def OpenChipController(self, chipController: ChipController):
        self.CloseChipController()
        self.chipController = chipController

        self.chipController.OnModified.Register(self.FileModified, True)
        self.chipController.OnSaved.Register(self.FileSaved, True)

        self.chipEditor.LoadChipController(self.chipController)
        self.chipParametersList.LoadChipController(self.chipController)
        self.valvesList.LoadChipController(self.chipController)

    def OnTabChanged(self):
        self.chipEditor.worldBrowser.SelectItem(None)

    def RequestAddBlock(self, lb: LogicBlock):
        lb.SetPosition(self.chipEditor.worldBrowser.GetCenterPoint())
        self.chipController.GetLogicBlock().AddSubBlock(lb)

    def RequestAddImage(self, image: Image):
        self.chipController.GetLogicBlock().AddImage(image)

    def FullFileName(self) -> typing.Optional[str]:
        return self.chipController.GetFilename()

    def FormattedFilename(self) -> str:
        return self.chipController.GetName()

    def CloseChipController(self):
        if self.chipController is not None:
            self.chipController.OnModified.Unregister(self.FileModified)
            self.chipController.OnSaved.Unregister(self.FileSaved)
            self.chipController.Destroy()
        self.chipEditor.Clear()
        self.chipParametersList.Clear()
        self.valvesList.Clear()
        self.chipController = None

    def RequestClose(self):
        if super().RequestClose():
            self.CloseChipController()
            return True
        return False

    def RequestNew(self):
        if self.RequestClose():
            self.OpenChip(ChipController())

    def TrySave(self):
        self.chipController.Save()
        return True

    def TrySaveAs(self):
        dialog = SaveAsDialog(self)
        if dialog.exec_():
            filename = dialog.selectedFiles()

            if filename is not None:
                self.chipController.Save(filename[0])
                return True
            else:
                return False
        return False

    def UpdateFromSave(self):
        self.chipController.GetLogicBlock().ReloadFileSubBlocks()


class SaveAsDialog(QFileDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Save chip")
        self.setFileMode(QFileDialog.AnyFile)
        self.setAcceptMode(QFileDialog.AcceptSave)
        self.setNameFilters(["μChip Chip Controller (*.ucc)"])
