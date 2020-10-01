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

        self.editorFrame = MainWorkArea(self.rig, self.procedureRunner)
        self.editorFrame.OnTabNamesChanged.Register(self.UpdateName)

        self.updateWorker = ChipUpdateWorker(self.rig, self.procedureRunner)
        self.editorFrame.OnChipOpened.Register(self.updateWorker.SetChipController, True)

        self.menuBarWidget = MenuBar()

        self.menuBarWidget.OnOpen.Register(self.editorFrame.DisplayOpenDialog)
        self.menuBarWidget.OnNewLB.Register(lambda: self.editorFrame.OpenLogicBlock(None))
        self.menuBarWidget.OnNewChip.Register(lambda: self.editorFrame.RequestChipOpen(None))
        self.menuBarWidget.OnSaveAs.Register(lambda: self.editorFrame.RequestSave(True))
        self.menuBarWidget.OnSave.Register(lambda: self.editorFrame.RequestSave(False))

        self.setMenuWidget(self.menuBarWidget)

        r = QApplication.primaryScreen().geometry()
        self.move(QPoint(r.center().x(), 0))
        self.resize(QSize(int(r.width() / 2), r.height() - 300))

        self.setFocusPolicy(Qt.StrongFocus)

        self.editorFrame.RequestChipOpen()
        self.threadPool = QThreadPool()

        self.threadPool.start(self.updateWorker)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.editorFrame, stretch=1)
        container.setLayout(layout)

    def UpdateName(self):
        name = self.editorFrame.chipFrame.GetFrameTitle()
        self.setWindowTitle(name + " - μChip")

    def closeEvent(self, event: QCloseEvent):
        if self.procedureRunner.IsRunning() and not self.procedureRunner.StopProcedure(True):
            event.ignore()
            return
        if self.editorFrame.RequestCloseAllTabs():
            self.updateWorker.stop()
            super().closeEvent(event)
        else:
            event.ignore()
            return
