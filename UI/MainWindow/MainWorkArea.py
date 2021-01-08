from UI.Chip.ChipEditorFrame import *
from UI.Procedure.ProcedureEditorFrame import *
from UI.LogicBlock.CustomLogicBlockEditorFrame import *
from UI.MainWindow.MainToolbar import *
from UI.RigView.RigViewWidget import *
from Procedures.ProcedureRunner import *
from UI.ProceduresDialog import *
from UI.Chip.ChipParametersList import *
from UI.MainWindow.StatusBar import *


class MainWorkArea(QFrame):
    def __init__(self, rig: Rig, procedureRunner: ProcedureRunner):
        super().__init__()

        self.rig = rig
        self.procedureRunner = procedureRunner
        self.procedureRunner.OnBegin.Register(lambda: self.UpdateForProcedureStatus(True))
        self.procedureRunner.OnDone.Register(lambda: self.UpdateForProcedureStatus(False))

        self.toolBar = MainToolbar()
        self.toolBar.OnNewLB.Register(lambda: self.OpenLogicBlock(None))
        self.toolBar.OnNewChip.Register(lambda: self.RequestChipOpen(None))
        self.toolBar.OnOpen.Register(self.DisplayOpenDialog)
        self.toolBar.OnSaveAs.Register(lambda: self.RequestSave(True))
        self.toolBar.OnSave.Register(lambda: self.RequestSave(False))
        self.toolBar.OnAddLogicBlock.Register(self.AddLogicBlock)
        self.toolBar.OnAddImage.Register(self.AddImage)
        self.toolBar.OnNewProcedure.Register(self.AddProcedure)
        self.toolBar.OnProcedureSelected.Register(self.SelectProcedure)
        self.toolBar.OnProcedurePlay.Register(lambda: self.procedureRunner.RunProcedure())
        self.toolBar.OnProcedureStop.Register(lambda: self.procedureRunner.StopProcedure(True))
        self.toolBar.OnManageProcedures.Register(self.ShowProceduresDialog)
        self.toolBar.OnOpenRig.Register(self.ShowRig)

        self.statusBar = StatusBar()

        self.chipParametersList = ChipParametersList()
        self.valvesList = ChipValvesList()

        self.chipFrame = ChipEditorFrame(rig)
        self.chipFrame.OnTitleUpdated.Register(self.UpdateTabNames)
        self.procedureFrame = ProcedureEditorFrame()
        self.procedureFrame.OnTitleUpdated.Register(self.UpdateTabNames)

        self.OnTabNamesChanged = Event()
        self.OnChipOpened = Event()

        self.tabArea = QTabWidget(self)
        self.tabArea.setTabPosition(QTabWidget.South)
        self.tabArea.setTabsClosable(True)
        self.tabArea.addTab(self.chipFrame, QIcon("Assets/icon.png"), "Chip Tab")
        self.tabArea.addTab(self.procedureFrame, "Procedures")
        self.tabArea.tabBar().setTabButton(0, QTabBar.RightSide, None)
        self.tabArea.tabBar().setTabButton(1, QTabBar.RightSide, None)
        self.tabArea.currentChanged.connect(self.SwitchTabs)
        self.tabArea.tabCloseRequested.connect(self.OnTabCloseRequest)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebarLayout = QVBoxLayout()
        sidebarLayout.setContentsMargins(0, 0, 0, 0)
        sidebarLayout.setSpacing(0)
        sidebarLayout.addWidget(self.chipParametersList)
        sidebarLayout.addWidget(self.valvesList)
        layout.addWidget(self.toolBar, stretch=0)

        innerLayout = QHBoxLayout()
        innerLayout.setContentsMargins(0, 0, 0, 0)
        innerLayout.setSpacing(0)
        innerLayout.addLayout(sidebarLayout)
        innerLayout.addWidget(self.tabArea, stretch=1)

        layout.addLayout(innerLayout, stretch=1)
        layout.addWidget(self.statusBar, stretch=0)
        self.setLayout(layout)

        self.currentEditorFrame: typing.Optional[BaseEditorFrame] = None
        self.SwitchTabs(0)

    def SwitchTabs(self, tabIndex):
        if self.currentEditorFrame is not None:
            self.currentEditorFrame.ClearFocus()

        self.currentEditorFrame = self.tabArea.widget(tabIndex)

        if tabIndex == 0:
            self.toolBar.SetState(MainToolbar.STATE_CHIP_EDIT)
        elif tabIndex == 1:
            self.toolBar.SetState(MainToolbar.STATE_PROCEDURE_EDIT)
        elif tabIndex >= 2:
            self.toolBar.SetState(MainToolbar.STATE_LB_EDIT)

        self.tabArea.setCurrentIndex(tabIndex)

    def UpdateForProcedureStatus(self, isRunning):
        self.chipFrame.UpdateForProcedureStatus(isRunning)
        self.procedureFrame.UpdateForProcedureStatus(isRunning)
        self.toolBar.UpdateForProcedureStatus(isRunning)

        self.chipParametersList.setEnabled(not isRunning)
        self.valvesList.setEnabled(not isRunning)

        if isRunning:
            self.SwitchTabs(1)
        for i in range(2, self.tabArea.count()):
            self.tabArea.setTabEnabled(i, isRunning)

    def AddLogicBlock(self, lb: LogicBlock):
        self.currentEditorFrame.AddLogicBlock(lb)

    def AddImage(self, image: Image):
        self.currentEditorFrame.AddImage(image)

    def AddProcedure(self, p: Procedure):
        self.chipFrame.chipController.AddProcedure(p)
        self.SelectProcedure(p)

    def SelectProcedure(self, p: Procedure):
        self.procedureFrame.OpenProcedure(p)
        self.procedureRunner.SetProcedure(p)
        self.toolBar.procedureSelectionBox.SelectProcedure(p)
        self.SwitchTabs(1)

    def UpdateTabNames(self):
        self.OnTabNamesChanged.Invoke()
        for i in range(self.tabArea.count()):
            frame = self.tabArea.widget(i)
            self.tabArea.setTabText(i, frame.GetFrameTitle())

    def GetWindowTitle(self):
        return self.chipFrame.FormattedFilename() + " - μChip"

    def OpenLogicBlock(self, filename=None):
        if filename is None:
            lb = CompoundLogicBlock()
        else:
            for i in reversed(range(2, self.tabArea.count())):
                frame = typing.cast(CustomLogicBlockEditorFrame, self.widget(i))
                if frame.logicBlock.GetFilename() == filename:
                    self.tabArea.setCurrentIndex(i)
                    return
            lb = CompoundLogicBlock.LoadFromFile(filename)

        newEditor = CustomLogicBlockEditorFrame(lb)
        newEditor.OnTitleUpdated.Register(self.UpdateTabNames)
        self.tabArea.addTab(newEditor, newEditor.GetFrameTitle())
        self.tabArea.setCurrentIndex(self.tabArea.count() - 1)

    def RequestChipOpen(self, filename=None):
        if not self.chipFrame.RequestClose():
            return

        if filename is None:
            cc = ChipController()
        else:
            cc = ChipController.LoadFromFile(filename)

        self.OpenChipController(cc)

    def OpenChipController(self, cc: ChipController):
        self.chipFrame.OpenChipController(cc)
        self.toolBar.SetChipController(cc)
        self.chipParametersList.SetChipController(cc)
        self.valvesList.SetChipController(cc)
        self.OnChipOpened.Invoke(cc)

        self.SelectProcedure(cc.GetProcedures()[0])

        self.SwitchTabs(0)

    def RequestSave(self, saveAs=False):
        if self.currentEditorFrame == self.procedureFrame:
            toSave = self.chipFrame
        else:
            toSave = self.currentEditorFrame

        if toSave.RequestSave(saveAs):
            for i in range(self.tabArea.count()):
                self.tabArea.widget(i).UpdateFromSave()

    def RequestCloseAllTabs(self):
        for i in reversed(range(2, self.tabArea.count())):
            if not self.OnTabCloseRequest(i):
                return False
        if not self.chipFrame.RequestClose():
            return False
        return True

    def OnTabCloseRequest(self, i):
        if i <= 1:
            return False
        frame = typing.cast(CustomLogicBlockEditorFrame, self.tabArea.widget(i))
        if frame.RequestClose():
            frame.OnTitleUpdated.Unregister(self.UpdateTabNames)
            frame.close()
            frame.deleteLater()
            return True
        return False

    def DisplayOpenDialog(self):
        dialog = OpenDialog(self)
        if dialog.exec_():
            filename = dialog.selectedFiles()
            if filename is not None:
                name, extension = os.path.splitext(filename[0])
                if extension == '.ucc':
                    self.RequestChipOpen(filename[0])
                elif extension == '.ulb':
                    self.OpenLogicBlock(filename[0])

    def ShowProceduresDialog(self):
        d = ProceduresDialog(self.chipFrame.chipController, parent=self)
        d.finished.connect(self.OnProcedureDialogFinished)
        d.exec_()

    def OnProcedureDialogFinished(self):
        self.UpdateTabNames()
        self.toolBar.procedureSelectionBox.UpdateProceduresList()

    def ShowRig(self):
        rigViewWidget = RigViewWidget(self.rig, parent=self)
        rigViewWidget.exec_()


class OpenDialog(QFileDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Open a file")
        self.setFileMode(QFileDialog.ExistingFile)
        self.setAcceptMode(QFileDialog.AcceptOpen)
        self.setNameFilters(["μChip File (*.ucc *.ulb)", "μChip Chip (*.ucc)", "μChip Logic Block (*.ulb)"])
