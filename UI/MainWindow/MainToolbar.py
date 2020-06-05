from PySide2.QtWidgets import *
from Util import *
from LogicBlocks.NumberBlocks import *
from LogicBlocks.BooleanBlocks import *
from LogicBlocks.ConditionalBlocks import *
from UI.Procedure.ProceduresBox import *
from LogicBlocks.IOBlocks import *
from PySide2.QtGui import *
from ChipController.ChipController import *


class MainToolbar(QFrame):
    def __init__(self, currentParameterMenu, setParameterMenu):
        super().__init__()

        self.buttons: typing.List[QAbstractButton] = []

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignLeft)
        layout.setSpacing(0)
        self.setLayout(layout)

        self.OnNewProcedure = Event()
        self.OnNewChip = Event()
        self.OnNewLB = Event()
        self.OnOpen = Event()
        self.OnSave = Event()
        self.OnSaveAs = Event()
        self.OnProcedureSelected = Event()
        self.OnManageProcedures = Event()
        self.OnProcedurePlay = Event()
        self.OnProcedureStop = Event()
        self.OnOpenRig = Event()

        self.OnAddLogicBlock = Event()
        self.OnAddImage = Event()

        self.fileMenuSection = self.AddMenuSection("File", 2, 3)
        self.fileMenuSection.addWidget(self.AddButton("Assets/chipIconPlus.png", "New Chip", self.OnNewChip.Invoke), 0,
                                       0)
        self.fileMenuSection.addWidget(self.AddButton("Assets/LBIconPlus.png", "New Logic Block", self.OnNewLB.Invoke),
                                       1, 0)
        self.fileMenuSection.addWidget(self.AddButton("Assets/openIcon.png", "Open...", self.OnOpen.Invoke, above=True),
                                       0, 1, 2, 1)
        self.fileMenuSection.addWidget(self.AddButton("Assets/saveIcon.png", "Save", self.OnSave.Invoke), 0, 2)
        self.fileMenuSection.addWidget(self.AddButton("Assets/saveAsIcon.png", "Save As...", self.OnSaveAs.Invoke), 1,
                                       2)

        mathMenu = self.LogicBlockMenu([NumberLogicBlock,
                                        Add,
                                        Subtract,
                                        Multiply,
                                        Divide,
                                        Modulus,
                                        Exponent,
                                        LShift,
                                        RShift,
                                        BAnd,
                                        BOr,
                                        BNot,
                                        Round,
                                        Ceiling,
                                        Floor])

        logicMenu = self.LogicBlockMenu([BooleanLogicBlock,
                                         AndLogicBlock,
                                         OrLogicBlock,
                                         NotLogicBlock])

        conditionalsMenu = self.LogicBlockMenu([IfLogicBlock,
                                                EqualsBlock,
                                                NEqualsBlock,
                                                LThanBlock,
                                                GThanBlock,
                                                LThanEBlock,
                                                GThanEBlock])

        testMenu = QMenu(self)
        testMenu.addAction("test")

        color = QColor(230, 230, 230)
        self.logicBlocksSection = self.AddMenuSection("Control Elements", 2, 3)
        self.logicBlocksSection.addWidget(self.AddButton("Assets/mathIcon.png", "Math", menu=mathMenu, color=color), 0,
                                          0)
        self.logicBlocksSection.addWidget(self.AddButton("Assets/logicIcon.png", "Logic", menu=logicMenu, color=color),
                                          1, 0)
        self.logicBlocksSection.addWidget(
            self.AddButton("Assets/conditionalIcon.png", "Conditionals", menu=conditionalsMenu, color=color),
            0, 1)
        self.logicBlocksSection.addWidget(
            self.AddButton("Assets/timeIcon.png", "Time", delegate=lambda: self.OnAddLogicBlock.Invoke(Time()),
                           color=color), 1, 1)
        self.logicBlocksSection.addWidget(
            self.AddButton("Assets/LBIcon.png", "Custom...", delegate=self.BrowseForBlock, above=True), 0, 2, 2, 1)

        self.chipSection = self.AddMenuSection("Chip Elements", 2, 2)
        self.chipSection.addWidget(self.AddButton("Assets/checkboxIcon.png", "YES/NO Parameter", color=color,
                                                  delegate=lambda: self.OnAddLogicBlock.Invoke(InputLogicBlock(bool))),
                                   0, 0)
        self.chipSection.addWidget(self.AddButton("Assets/numberIcon.png", "Number Parameter", color=color,
                                                  delegate=lambda: self.OnAddLogicBlock.Invoke(InputLogicBlock(float))),
                                   1, 0)
        self.chipSection.addWidget(self.AddButton("Assets/valveIcon.png", "Valve", color=color, above=True,
                                                  delegate=lambda: self.OnAddLogicBlock.Invoke(ValveLogicBlock())), 0,
                                   1, 2, 1)

        self.procedureElementsSection = self.AddMenuSection("Procedure Elements",
                                                            2, 3)
        self.procedureElementsSection.addWidget(self.AddButton("Assets/timeIcon.png", "Wait Step", color=color,
                                                               delegate=lambda: self.OnAddLogicBlock.Invoke(
                                                                   WaitStep())), 0, 0)
        self.procedureElementsSection.addWidget(self.AddButton("Assets/conditionalIcon.png", "Decision", color=color,
                                                               delegate=lambda: self.OnAddLogicBlock.Invoke(IfStep())),
                                                1, 0)

        self.procedureElementsSection.addWidget(self.AddButton(None, "Current Parameter", menu=currentParameterMenu), 0,
                                                1)
        self.procedureElementsSection.addWidget(self.AddButton(None, "Set Parameter", menu=setParameterMenu), 1, 1)

        self.ioSection = self.AddMenuSection("Input/Output", 2, 2)
        self.ioSection.addWidget(self.AddButton("Assets/checkboxIcon.png", "YES/NO Input", color=color,
                                                delegate=lambda: self.OnAddLogicBlock.Invoke(InputLogicBlock(bool))), 0,
                                 0)
        self.ioSection.addWidget(self.AddButton("Assets/numberIcon.png", "Number Input", color=color,
                                                delegate=lambda: self.OnAddLogicBlock.Invoke(InputLogicBlock(float))),
                                 1, 0)
        self.ioSection.addWidget(self.AddButton("Assets/checkboxIcon.png", "YES/NO Output", color=color,
                                                delegate=lambda: self.OnAddLogicBlock.Invoke(OutputLogicBlock(bool))),
                                 0, 1)
        self.ioSection.addWidget(self.AddButton("Assets/numberIcon.png", "Number Output", color=color,
                                                delegate=lambda: self.OnAddLogicBlock.Invoke(OutputLogicBlock(float))),
                                 1, 1)

        self.annotationSection = self.AddMenuSection("Other", 1, 1)
        self.annotationSection.addWidget(
            self.AddButton("Assets/imageIcon.png", "Image", above=True, delegate=self.BrowseForImage, color=color), 0,
            0)

        self.proceduresSection = self.AddMenuSection("Procedures", 2, 1)

        t = QFrame()
        t.setLayout(QHBoxLayout())
        t.layout().setContentsMargins(0, 0, 0, 0)
        t.layout().setSpacing(0)
        self.proceduresBox = ProceduresBox()
        self.proceduresBox.OnProcedureSelected.Register(self.OnProcedureSelected.Invoke)
        self.playButton = self.AddButton("Assets/playIcon.png", "Run Procedure", color=QColor(0, 255, 0),
                                         delegate=self.OnProcedurePlay.Invoke,
                                         showText=False)
        self.stopButton = self.AddButton("Assets/stopIcon.png", "Stop Procedure", color=QColor(255, 0, 0),
                                         delegate=self.OnProcedureStop.Invoke,
                                         showText=False)
        self.addButton = self.AddButton("Assets/plusIcon.png", "New Procedure", color=color, showText=False,
                                        delegate=self.PromptNewProcedure)

        t.layout().addWidget(self.playButton)
        t.layout().addWidget(self.stopButton)
        t.layout().addWidget(self.proceduresBox)
        t.layout().addWidget(self.addButton)

        self.proceduresSection.addWidget(t, 0, 0)

        self.proceduresSection.addWidget(
            self.AddButton("Assets/listIcon.png", "Manage...", color=color, delegate=self.OnManageProcedures.Invoke), 1,
            0)

        self.rigButton = self.AddButton("Assets/solenoidsIcon.png", "Open Rig...", above=True,
                                        delegate=self.OnOpenRig.Invoke,
                                        color=color)
        self.solenoidsSection = self.AddMenuSection("Rig", 1, 1)
        self.solenoidsSection.addWidget(self.rigButton, 0, 0)

        layout.addLayout(self.fileMenuSection)
        layout.addLayout(self.logicBlocksSection)
        layout.addLayout(self.chipSection)
        layout.addLayout(self.procedureElementsSection)
        layout.addLayout(self.ioSection)
        layout.addLayout(self.proceduresSection)
        layout.addLayout(self.annotationSection)
        layout.addLayout(self.solenoidsSection)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    STATE_CHIP_EDIT = 1
    STATE_PROCEDURE_EDIT = 2
    STATE_LB_EDIT = 4

    def SetState(self, state):
        offChildren = []
        onChildren = []
        for child in [self.chipSection.itemAt(x).widget() for x in range(self.chipSection.count())]:
            if state == MainToolbar.STATE_CHIP_EDIT:
                onChildren.append(child)
            else:
                offChildren.append(child)
        for child in [self.procedureElementsSection.itemAt(x).widget() for x in
                      range(self.procedureElementsSection.count())]:
            if state == MainToolbar.STATE_PROCEDURE_EDIT:
                onChildren.append(child)
            else:
                offChildren.append(child)
        for child in [self.ioSection.itemAt(x).widget() for x in range(self.ioSection.count())]:
            if state == MainToolbar.STATE_LB_EDIT:
                onChildren.append(child)
            else:
                offChildren.append(child)

        for off in offChildren:
            off.setVisible(False)

        for on in onChildren:
            on.setVisible(True)

        self.updateGeometry()

    def SetIsProcedureRunning(self, isRunning):
        self.proceduresBox.setEnabled(not isRunning)

        self.stopButton.setVisible(isRunning)
        self.playButton.setVisible(not isRunning)

        for b in self.buttons:
            b.setEnabled(not isRunning)

        self.stopButton.setEnabled(isRunning)
        self.rigButton.setEnabled(True)

    def AddButton(self, icon, text, delegate=None, menu=None, above=False, showText=True, color=None):
        if above is True or not showText:
            b = QToolButton()
            if showText:
                b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        else:
            text = "  " + text
            b = QPushButton()

        b.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        if icon is not None:
            b.setIcon(ColorIcon(icon, color))

        b.setIconSize(QSize(32, 32))
        b.setText(text)
        b.setToolTip(text)
        b.clicked.connect(delegate)

        if menu is not None:
            b.setMenu(menu)

        self.buttons.append(b)

        return b

    def AddMenuSection(self, name, r, c):
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        label = QLabel(name)
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("SectionTitle")
        layout.addWidget(label, r, 0, 1, c)

        stretch = QFrame()
        stretch.setContentsMargins(0, 0, 0, 0)
        stretch.setFixedWidth(10)
        stretch.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        stretch.setObjectName("SectionSpacer")
        layout.addWidget(stretch, 0, c, r + 1, 1)

        return layout

    def LogicBlockMenu(self, blocks: typing.List[typing.Type[LogicBlock]]):
        menu = QMenu(self)
        for block in blocks:
            newAction = menu.addAction(block.GetName())
            newAction.triggered.connect(lambda checked=False, b=block: self.OnAddLogicBlock.Invoke(b()))
        return menu

    def BrowseForBlock(self):
        dialog = BrowseForCustomDialog(self)
        if dialog.exec_():
            filename = dialog.selectedFiles()

            if filename is not None:
                newBlock = CompoundLogicBlock.LoadFromFile(filename[0])
                self.OnAddLogicBlock.Invoke(newBlock)

    def BrowseForImage(self):
        dialog = BrowseForImageDialog(self)
        if dialog.exec_():
            filename = dialog.selectedFiles()

            if filename is not None:
                newImage = Image(filename[0])
                self.OnAddImage.Invoke(newImage)

    def PromptNewProcedure(self):
        (text, ok) = QInputDialog.getText(self, "New Procedure", "Procedure Name:")

        if ok and text:
            newProcedure = Procedure()
            newProcedure.SetName(text)
            self.OnNewProcedure.Invoke(newProcedure)


class BrowseForImageDialog(QFileDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Open a in image")
        self.setFileMode(QFileDialog.ExistingFile)
        self.setAcceptMode(QFileDialog.AcceptOpen)
        self.setNameFilters(["Image file (*.bmp *.gif *.jpg *.jpeg *.png *.pbm *.pgm *.ppm *.xbm *.xpm)"])


class BrowseForCustomDialog(QFileDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Open a logic block")
        self.setFileMode(QFileDialog.ExistingFile)
        self.setAcceptMode(QFileDialog.AcceptOpen)
        self.setNameFilters(["μChip Logic Block (*.ulb)"])
