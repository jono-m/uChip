from UI.MainWindow.MainWorkArea import *
from UI.MainWindow.MenuBar import *
from ChipController.ChipUpdateWorker import *
from UI.STYLESHEET import stylesheet


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setStyleSheet(stylesheet)

        container = QFrame()
        container.setObjectName("Container")
        container.setFrameShape(QFrame.NoFrame)
        self.setCentralWidget(container)

        icon = QIcon("Assets/icon.png")
        self.setWindowIcon(icon)

        self.rig = Rig()

        self.procedureRunner = ProcedureRunner()
        self.procedureRunner.OnBegin.Register(lambda: self.menuBarWidget.UpdateForProcedureStatus(True))
        self.procedureRunner.OnDone.Register(lambda: self.menuBarWidget.UpdateForProcedureStatus(False))

        self.workArea = MainWorkArea(self.rig, self.procedureRunner)
        self.workArea.OnTabNamesChanged.Register(self.UpdateName)

        self.updateWorker = ChipUpdateWorker(self.rig, self.procedureRunner)
        self.workArea.OnChipOpened.Register(self.updateWorker.SetChipController, True)

        self.menuBarWidget = MenuBar()

        self.menuBarWidget.OnOpen.Register(self.workArea.DisplayOpenDialog)
        self.menuBarWidget.OnNewLB.Register(lambda: self.workArea.OpenLogicBlock(None))
        self.menuBarWidget.OnNewChip.Register(lambda: self.workArea.RequestChipOpen(None))
        self.menuBarWidget.OnSaveAs.Register(lambda: self.workArea.RequestSave(True))
        self.menuBarWidget.OnSave.Register(lambda: self.workArea.RequestSave(False))

        self.setMenuWidget(self.menuBarWidget)

        self.setFocusPolicy(Qt.StrongFocus)

        self.workArea.RequestChipOpen()
        self.threadPool = QThreadPool()

        self.threadPool.start(self.updateWorker)

        layout = QHBoxLayout()
        layout.addWidget(self.workArea)
        container.setLayout(layout)

        self.procedureRunner.StopProcedure()

    def UpdateName(self):
        name = self.workArea.chipFrame.GetFrameTitle()
        self.setWindowTitle(name + " - μChip")

    def closeEvent(self, event: QCloseEvent):
        if self.procedureRunner.IsRunning() and not self.procedureRunner.StopProcedure(True):
            event.ignore()
            return
        if self.workArea.RequestCloseAllTabs():
            self.updateWorker.stop()
            super().closeEvent(event)
        else:
            event.ignore()
            return
