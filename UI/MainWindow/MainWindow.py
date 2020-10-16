from UI.MainWindow.MainWorkArea import *
from UI.MainWindow.MenuBar import *
from ChipController.ChipUpdateWorker import *
from UI.StylesheetLoader import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        StylesheetLoader.GetInstance().RegisterWidget(self)

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.workArea)
        container.setLayout(layout)

        self.procedureRunner.StopProcedure()

        self.ReloadSettings()

    def SaveSettings(self):
        windowSettings = WindowSettings()
        windowSettings.maximized = self.isMaximized()
        windowSettings.position = self.pos()
        windowSettings.size = self.size()
        file = open("windowSettings.pkl", "wb")
        pickle.dump(windowSettings, file)
        file.close()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.SaveSettings()

    def moveEvent(self, event: QMoveEvent):
        super().moveEvent(event)
        self.SaveSettings()

    def ReloadSettings(self):
        windowSettings = WindowSettings()
        if os.path.exists("windowSettings.pkl"):
            file = open("windowSettings.pkl", "rb")
            windowSettings = pickle.load(file)

        self.resize(windowSettings.size)
        self.move(windowSettings.position)
        if windowSettings.maximized:
            self.showMaximized()
        else:
            self.showNormal()

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


class WindowSettings:
    size = QSize(1000, 1200)
    position = QPoint(100, 100)
    maximized = False
