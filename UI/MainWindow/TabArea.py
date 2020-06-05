from UI.Chip.ChipFrame import *
from UI.Procedure.ProcedureFrame import *
from UI.LogicBlock.LogicBlockFrame import *


class TabArea(QTabWidget):
    def __init__(self, rig: Rig):
        super().__init__()

        self.setTabPosition(QTabWidget.South)
        self.chipTab = ChipFrame(rig)
        self.chipTab.OnNameChange.Register(self.UpdateNames)
        self.procedureTab = ProcedureFrame()
        self.addTab(self.chipTab, QIcon("Assets/icon.png"), "Chip Tab")
        self.addTab(self.procedureTab, "Procedures")
        self.setTabsClosable(True)

        self.OnNameChange = Event()
        self.OnChipOpened = Event()
        self.OnProcedureOpened = Event()

        self.tabBar().setTabButton(0, QTabBar.RightSide, None)
        self.tabBar().setTabButton(1, QTabBar.RightSide, None)

        self.currentChanged.connect(self.OnTabChanged)
        self.tabCloseRequested.connect(self.OnTabCloseRequest)

    def OnTabChanged(self):
        for i in range(self.count()):
            frame = self.widget(i)
            frame.OnTabChanged()

    def SetIsProcedureRunning(self, isRunning):
        self.chipTab.SetIsProcedureRunning(isRunning)
        self.procedureTab.SetIsProcedureRunning(isRunning)
        if isRunning:
            self.setCurrentIndex(1)
        for i in range(2, self.count()):
            self.setTabEnabled(i, isRunning)

    def RequestAddBlock(self, lb: LogicBlock):
        self.currentWidget().RequestAddBlock(lb)

    def RequestAddImage(self, image: Image):
        self.currentWidget().RequestAddImage(image)

    def RequestAddProcedure(self, p: Procedure):
        self.procedureTab.chipController.AddProcedure(p)
        self.procedureTab.OpenProcedure(p)
        self.OnProcedureOpened.Invoke(p)
        self.setCurrentIndex(1)
        self.UpdateNames()

    def RequestSelectProcedure(self, p: Procedure):
        self.procedureTab.OpenProcedure(p)
        self.OnProcedureOpened.Invoke(p)
        self.setCurrentIndex(1)
        self.UpdateNames()

    def UpdateNames(self):
        self.OnNameChange.Invoke()
        for i in range(self.count()):
            frame = self.widget(i)
            self.setTabText(i, frame.GetFrameTitle())

    def GetWindowTitle(self):
        return self.chipTab.FormattedFilename() + " - μChip"

    def RequestLBOpen(self, filename=None):
        if filename is None:
            lb = CompoundLogicBlock()
        else:
            for i in reversed(range(2, self.count())):
                frame = typing.cast(LogicBlockFrame, self.widget(i))
                if frame.logicBlock.GetFilename() == filename:
                    self.setCurrentIndex(i)
                    return
            lb = CompoundLogicBlock.LoadFromFile(filename)

        newEditor = LogicBlockFrame(lb)
        newEditor.OnNameChange.Register(self.UpdateNames)
        self.addTab(newEditor, newEditor.GetFrameTitle())
        self.setCurrentIndex(self.count() - 1)

    def RequestChipOpen(self, filename=None):
        if not self.chipTab.RequestClose():
            return
        
        if filename is None:
            cc = ChipController()
        else:
            cc = ChipController.LoadFromFile(filename)

        self.chipTab.OpenChipController(cc)
        self.procedureTab.OpenChipController(cc)
        self.OnChipOpened.Invoke(cc)
        self.OnProcedureOpened.Invoke(cc.GetProcedures()[0])
        self.setCurrentIndex(0)
        self.UpdateNames()

    def RequestSave(self, saveAs=False):
        current = self.currentWidget()

        didSave = False
        if isinstance(current, LogicBlockFrame):
            if current.RequestSave(saveAs):
                didSave = True
        else:
            if self.chipTab.RequestSave(saveAs):
                didSave = True

        if didSave:
            for i in range(self.count()):
                self.widget(i).UpdateFromSave()

    def RequestClose(self):
        for i in reversed(range(2, self.count())):
            if not self.OnTabCloseRequest(i):
                return False
        if not self.chipTab.RequestClose():
            return False
        return True

    def OnTabCloseRequest(self, i):
        frame = typing.cast(LogicBlockFrame, self.widget(i))
        if frame.RequestClose():
            frame.OnNameChange.Unregister(self.UpdateNames)
            frame.close()
            frame.deleteLater()
            return True
        return False
