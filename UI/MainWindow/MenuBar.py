from Util import *


class MenuBar(QFrame):
    def __init__(self):
        super().__init__()
        self.OnNewChip = Event()
        self.OnNewLB = Event()
        self.OnOpen = Event()
        self.OnSave = Event()
        self.OnSaveAs = Event()

        self.menuBar = QMenuBar()
        self.menuBar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        fileMenu = self.menuBar.addMenu("&File")
        newChipAction = QAction(QIcon("Assets/UCIcon.png"), "New Chip", self)
        newChipAction.setShortcut(Qt.CTRL + Qt.Key_N)
        newChipAction.triggered.connect(self.OnNewChip.Invoke)
        newLBAction = QAction(QIcon("Assets/LBIcon.png"), "New Logic Block", self)
        newLBAction.triggered.connect(self.OnNewLB.Invoke)
        newLBAction.setShortcut(Qt.CTRL + Qt.SHIFT + Qt.Key_N)
        openAction = QAction("Open...", self)
        openAction.setShortcut(Qt.CTRL + Qt.Key_O)
        openAction.triggered.connect(self.OnOpen.Invoke)
        saveAction = QAction("Save", self)
        saveAction.setShortcut(Qt.CTRL + Qt.Key_S)
        saveAction.triggered.connect(self.OnSave.Invoke)
        saveAsAction = QAction("Save As...", self)
        saveAsAction.setShortcut(Qt.CTRL + Qt.SHIFT + Qt.Key_S)
        saveAsAction.triggered.connect(self.OnSaveAs.Invoke)

        fileMenu.addAction(newChipAction)
        fileMenu.addAction(newLBAction)
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveAsAction)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        layout.addWidget(self.menuBar)

    def UpdateForProcedureStatus(self, isRunning):
        self.setEnabled(not isRunning)
