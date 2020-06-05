from UI.MainWindow.TabArea import *
from UI.MainWindow.MainToolbar import *
from UI.MainWindow.MenuBar import *
from UI.Procedure.ProcedureMenu import *
from Procedures.ProcedureRunner import *
from UI.ProceduresDialog import *
from UI.RigView.RigViewWidget import *
from UI.MainWindow.UpdaterThreading import *
import os
from ChipController.ChipUpdateWorker import *


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
        #Container {
            border-width: 2px;
        }
        *, QTabBar {
            background-color: rgba(65, 65, 65, 1);
            border-color: rgba(80, 80, 80, 1);
            color: rgba(230, 230, 230, 1);
            border-style: solid;
            border-width: 0px;
       } 
       MenuBar {
            border-width: 0px 2px 0px 2px;
       }
        QMenuBar::item:selected, QMenu::item:selected {
            background-color: rgba(0, 0, 0, 0.3);
            color: white;
        }
        QPushButton, QToolButton {
            background-color: rgba(0, 0, 0, 0.05);
            text-align: left;
            padding: 10px;
            border-width: 1px;
        }
        #menuBarButton {
            border: none;
        }
        QPushButton:hover, QToolButton:hover{
            background-color: rgba(0, 0, 0, 0.3);
        }
        QPushButton:pressed, QToolButton:pressed {
            background-color: rgba(0, 0, 0, 0.4);
        }
        QPushButton:disabled, QToolButton:disabled {
            color: rgba(100, 100, 100, 1);
        }
        QTabWidget::pane {
            border: none;
        }
        QTabBar::tab {
            background-color: rgba(255, 255, 255, 0.05);
        }
        QTabBar::tab:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }
        QTabBar::tab:selected {
            background-color: rgba(232, 200, 93, 1);
            color: black;
        }
        QTabBar::close-button {
            image: url(Assets/closeIcon.png);
        }
        QGraphicsView {
            border: 5px inset rgba(30, 30, 30, 1);
        }
        #SectionTitle {
            background-color: rgba(0, 0, 0, 0.2);
        }
        #SectionSpacer {
            background-color: transparent;
        }
        QComboBox {
            color: white;
            padding: 0 0 0 20px;
            border: 1px solid rgba(255, 255, 255, 0.5);
        }
        QComboBox:drop-down {
            width: 32px;
            background-color: transparent;
        }
        QComboBox:down-arrow {
            image: url(Assets/downArrow.png);
            width: 16px;
            height: 16px;
        }
        QComboBox QAbstractItemView::item, QListWidget::item { 
            min-height: 50px; min-width: 50px;
        }
        QListView, QLineEdit {
            border: 1px solid rgba(255, 255, 255, 0.5);
        }
        QListView::item:selected { 
            background-color: rgba(0, 0, 0, 0.2);
        }
        """)

        container = QFrame()
        container.setObjectName("Container")
        container.setFrameShape(QFrame.NoFrame)
        self.setCentralWidget(container)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        container.setLayout(layout)

        icon = QIcon("Assets/icon.png")
        self.setWindowIcon(icon)

        self.rig = Rig()

        self.tabArea = TabArea(self.rig)
        self.tabArea.OnNameChange.Register(self.UpdateName)
        self.tabArea.currentChanged.connect(self.OnTabChanged)

        self.getMenu = GetMenu()
        self.setMenu = SetMenu()

        self.procedureRunner = ProcedureRunner()
        self.procedureRunner.OnBegin.Register(lambda: self.SetProcedureRunning(True))
        self.procedureRunner.OnDone.Register(lambda: self.SetProcedureRunning(False))

        self.updateWorker = ChipUpdateWorker(self.rig, self.procedureRunner)

        self.toolBar = MainToolbar(self.getMenu, self.setMenu)
        self.toolBar.OnNewLB.Register(lambda: self.tabArea.RequestLBOpen(None))
        self.toolBar.OnNewChip.Register(lambda: self.tabArea.RequestChipOpen(None))
        self.toolBar.OnOpen.Register(self.DisplayOpenDialog)
        self.toolBar.OnSaveAs.Register(lambda: self.tabArea.RequestSave(True))
        self.toolBar.OnSave.Register(lambda: self.tabArea.RequestSave(False))
        self.toolBar.OnAddLogicBlock.Register(self.tabArea.RequestAddBlock)
        self.toolBar.OnAddImage.Register(self.tabArea.RequestAddImage)
        self.toolBar.OnNewProcedure.Register(self.tabArea.RequestAddProcedure)
        self.toolBar.OnProcedureSelected.Register(self.tabArea.RequestSelectProcedure)
        self.toolBar.OnProcedurePlay.Register(
            lambda: self.procedureRunner.RunProcedure(self.toolBar.proceduresBox.currentProcedure))
        self.toolBar.OnProcedureStop.Register(lambda: self.procedureRunner.StopProcedure(True))
        self.toolBar.OnManageProcedures.Register(self.ManageProcedures)
        self.toolBar.OnOpenRig.Register(self.ShowRig)

        self.tabArea.OnChipOpened.Register(self.toolBar.proceduresBox.SetChipController, True)
        self.tabArea.OnChipOpened.Register(self.getMenu.SetChipController, True)
        self.tabArea.OnChipOpened.Register(self.setMenu.SetChipController, True)
        self.tabArea.OnChipOpened.Register(self.updateWorker.SetChipController, True)

        self.getMenu.OnAddGet.Register(self.tabArea.RequestAddBlock, True)
        self.setMenu.OnAddSet.Register(self.tabArea.RequestAddBlock, True)

        layout.addWidget(self.toolBar)
        layout.addWidget(self.tabArea)

        self.menuBarWidget = MenuBar()

        self.menuBarWidget.OnOpen.Register(self.DisplayOpenDialog)
        self.menuBarWidget.OnNewLB.Register(lambda: self.tabArea.RequestLBOpen(None))
        self.menuBarWidget.OnNewChip.Register(lambda: self.tabArea.RequestChipOpen(None))
        self.menuBarWidget.OnSaveAs.Register(lambda: self.tabArea.RequestSave(True))
        self.menuBarWidget.OnSave.Register(lambda: self.tabArea.RequestSave(False))

        self.setMenuWidget(self.menuBarWidget)

        r = QApplication.primaryScreen().geometry()
        self.move(QPoint(r.center().x(), 0))
        self.resize(QSize(int(r.width() / 2), r.height() - 300))

        self.rigViewWidget = RigViewWidget(self.rig, parent=self)

        self.setFocusPolicy(Qt.StrongFocus)

        self.OnTabChanged(0)

        self.tabArea.RequestChipOpen()

        self.SetProcedureRunning(False)

        self.threadPool = QThreadPool()

        self.threadPool.start(self.updateWorker)

    def ShowRig(self):
        self.rigViewWidget.show()
        self.rigViewWidget.update()

    def ManageProcedures(self):
        d = ProceduresDialog(self.tabArea.chipTab.chipController, parent=self)
        d.finished.connect(self.ManageDone)
        d.exec_()

    def ManageDone(self):
        self.tabArea.UpdateNames()
        self.toolBar.proceduresBox.UpdateProceduresList()

    def SetProcedureRunning(self, isRunning):
        self.toolBar.SetIsProcedureRunning(isRunning)
        self.menuBarWidget.SetIsProcedureRunning(isRunning)
        self.tabArea.SetIsProcedureRunning(isRunning)

    def OnTabChanged(self, i):
        if i == 0:
            self.toolBar.SetState(MainToolbar.STATE_CHIP_EDIT)
        elif i == 1:
            self.toolBar.SetState(MainToolbar.STATE_PROCEDURE_EDIT)
        elif i >= 2:
            self.toolBar.SetState(MainToolbar.STATE_LB_EDIT)

    def UpdateName(self):
        name = self.tabArea.chipTab.GetFrameTitle()
        self.setWindowTitle(name + " - μChip")

    def closeEvent(self, event: QCloseEvent):
        if self.procedureRunner.IsRunning() and not self.procedureRunner.StopProcedure(True):
            event.ignore()
            return
        if self.tabArea.RequestClose():
            self.updateWorker.stop()
            super().closeEvent(event)
        else:
            event.ignore()
            return

    def DisplayOpenDialog(self):
        dialog = OpenDialog(self)
        if dialog.exec_():
            filename = dialog.selectedFiles()
            if filename is not None:
                name, extension = os.path.splitext(filename[0])
                if extension == '.ucc':
                    self.tabArea.RequestChipOpen(filename[0])
                elif extension == '.ulb':
                    self.tabArea.RequestLBOpen(filename[0])


class OpenDialog(QFileDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Open a file")
        self.setFileMode(QFileDialog.ExistingFile)
        self.setAcceptMode(QFileDialog.AcceptOpen)
        self.setNameFilters(["μChip File (*.ucc *.ulb)", "μChip Chip (*.ucc)", "μChip Logic Block (*.ulb)"])
