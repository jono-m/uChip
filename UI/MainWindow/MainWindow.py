from UI.MainWindow.MainWorkArea import *
from UI.MainWindow.MenuBar import *
from BlockSystem.ChipController.ChipUpdateWorker import *
from UI.StylesheetLoader import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        StylesheetLoader.GetInstance().RegisterWidget(self)

        container = QFrame()
        container.setObjectName("Container")
        container.setFrameShape(QFrame.NoFrame)
        self.setCentralWidget(container)

        icon = QIcon("Images/icon.png")
        self.setWindowIcon(icon)

        self.rig = Rig()

        self.procedureRunner = ProcedureRunner(self)
        self.procedureRunner.onBegin.connect(lambda: self.menuBarWidget.UpdateForProcedureStatus(True))
        self.procedureRunner.onDone.connect(lambda: self.menuBarWidget.UpdateForProcedureStatus(False))
        self.procedureRunner.onInterruptRequest.connect(self.ShowInterruptDialog)
        self.procedureRunner.onCompleted.connect(self.ShowCompletedDialog)

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

        self._interruptDialog = None

    def ShowCompletedDialog(self):
        if self._interruptDialog is not None:
            self._interruptDialog.reject()
            self._interruptDialog = None
        msgBox = QMessageBox(self)
        msgBox.setIcon(QMessageBox.Icon.Information)
        msgBox.setWindowTitle("Procedure Completed")
        msgBox.setText("The procedure has finished.")
        msgBox.setStandardButtons(QMessageBox.Ok)
        ret = msgBox.exec()

    def ShowInterruptDialog(self):
        self._interruptDialog = QMessageBox(self)
        self._interruptDialog.setWindowTitle("Confirm Stop")
        self._interruptDialog.setIcon(QMessageBox.Icon.Warning)
        self._interruptDialog.setText("There is a procedure running")
        self._interruptDialog.setInformativeText("Are you sure that you want to stop?")
        self._interruptDialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        self._interruptDialog.setDefaultButton(QMessageBox.No)
        ret = self._interruptDialog.exec()
        if ret == QMessageBox.Yes:
            self.procedureRunner.ProcedureFinished(True)
        self._interruptDialog = None

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
        if self.procedureRunner.IsRunning():
            self.procedureRunner.StopProcedure(True)
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
