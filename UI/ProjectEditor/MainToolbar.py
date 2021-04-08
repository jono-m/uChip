from BlockSystem.Blocks.BooleanBlocks import *
from BlockSystem.Blocks.ConditionalBlocks import *
from BlockSystem.Blocks.NumberBlocks import *
from BlockSystem.Blocks.ScriptedBlock import *
from UI.Procedure.ProcedureMenu import *
from UI.Procedure.ProcedureSelectionBox import *
from UI.ProjectEditor.StatusBar import *


class ToolbarSection:
    def __init__(self, name):
        self.name = name
        self.elements: typing.List[typing.Tuple[QWidget, int, int, int, int]] = []
        self.titleBar = QLabel(name)
        self.spacer = Spacer()

    def AddElement(self, element: QWidget, row, column, rowSpan=1, columnSpan=1):
        self.elements.append((element, row, column, rowSpan, columnSpan))

    def SetVisible(self, visible: bool):
        for [element, _, _, _, _] in self.elements:
            element.setVisible(visible)
        self.titleBar.setVisible(visible)
        self.spacer.setVisible(visible)

    def AddToGridLayout(self, gridLayout: QGridLayout, currentColumn) -> int:
        nRows = 0
        nCols = 0
        for [element, row, column, rowSpan, columnSpan] in self.elements:
            gridLayout.addWidget(element, row, column + currentColumn, rowSpan, columnSpan)
            nRows = max(nRows, row + rowSpan)
            nCols = max(nCols, column + columnSpan)
        gridLayout.addWidget(self.titleBar, nRows, currentColumn, 1, nCols)
        gridLayout.addWidget(self.spacer, 0, currentColumn + nCols, nRows + 1, 1)
        return nCols + currentColumn + 1


class Spacer(QFrame):
    pass


class MainToolbar(QFrame):
    def __init__(self):
        super().__init__()
        self.buttons: typing.List[QAbstractButton] = []

        self.setObjectName("MainToolbar")

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignLeft)
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

        self.fileMenuSection = ToolbarSection("File")
        self.fileMenuSection.AddElement(
            self.CreateButton("Images/chipIconPlus.png", "New Chip", self.OnNewChip.Invoke, trueColor=True), 0, 0)
        self.fileMenuSection.AddElement(
            self.CreateButton("Images/LBIconPlus.png", "New Logic Block", self.OnNewLB.Invoke, trueColor=True), 1, 0)
        self.fileMenuSection.AddElement(
            self.CreateButton("Images/openIcon.png", "Open...", self.OnOpen.Invoke, above=True, trueColor=True), 0, 1,
            2, 1)
        self.fileMenuSection.AddElement(
            self.CreateButton("Images/saveIcon.png", "Save", self.OnSave.Invoke, trueColor=True), 0, 2)
        self.fileMenuSection.AddElement(
            self.CreateButton("Images/saveAsIcon.png", "Save As...", self.OnSaveAs.Invoke, trueColor=True), 1, 2)

        mathMenu = self.LogicBlockMenu([NumberConstantBlock,
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

        self.logicBlocksSection = ToolbarSection("Control Elements")
        self.logicBlocksSection.AddElement(
            self.CreateButton("Images/mathIcon.png", "Math", menu=mathMenu), 0, 0)
        self.logicBlocksSection.AddElement(
            self.CreateButton("Images/logicIcon.png", "Logic", menu=logicMenu), 1, 0)
        self.logicBlocksSection.AddElement(
            self.CreateButton("Images/conditionalIcon.png", "Conditionals", menu=conditionalsMenu), 0, 1)
        self.logicBlocksSection.AddElement(
            self.CreateButton("Images/timeIcon.png", "Time", delegate=lambda: self.OnAddLogicBlock.Invoke(Time())), 1,
            1)
        self.logicBlocksSection.AddElement(
            self.CreateButton("Images/LBIcon.png", "Custom...", delegate=self.BrowseForBlock, above=True,
                              trueColor=True), 0, 2, 2, 1)

        self.chipSection = ToolbarSection("Chip Elements")
        self.chipSection.AddElement(
            self.CreateButton("Images/checkboxIcon.png", "YES/NO Parameter",
                              delegate=lambda: self.OnAddLogicBlock.Invoke(InputLogicBlock(bool, True))), 0, 0)
        self.chipSection.AddElement(
            self.CreateButton("Images/numberIcon.png", "Number Parameter",
                              delegate=lambda: self.OnAddLogicBlock.Invoke(InputLogicBlock(float, True))), 1, 0)
        self.chipSection.AddElement(
            self.CreateButton("Images/valveIcon.png", "Valve", above=True,
                              delegate=lambda: self.OnAddLogicBlock.Invoke(ValveLogicBlock())), 0, 1, 2, 1)

        self.procedureElementsSection = ToolbarSection("Procedure Elements")
        self.procedureElementsSection.AddElement(
            self.CreateButton("Images/timeIcon.png", "Wait Step",
                              delegate=lambda: self.OnAddLogicBlock.Invoke(WaitStep())), 0, 0)
        self.procedureElementsSection.AddElement(
            self.CreateButton("Images/conditionalIcon.png", "Decision",
                              delegate=lambda: self.OnAddLogicBlock.Invoke(IfStep())), 1, 0)

        self.getMenu = GetMenu(self)
        self.setMenu = SetMenu(self)

        self.getMenu.OnAddGet.Register(self.OnAddLogicBlock.Invoke, True)
        self.setMenu.OnAddSet.Register(self.OnAddLogicBlock.Invoke, True)

        self.procedureElementsSection.AddElement(
            self.CreateButton(None, "Current Parameter", menu=self.getMenu), 0, 1)
        self.procedureElementsSection.AddElement(
            self.CreateButton(None, "Set Parameter", menu=self.setMenu), 1, 1)

        self.ioSection = ToolbarSection("Input/Output")
        self.ioSection.AddElement(
            self.CreateButton("Images/checkboxIcon.png", "YES/NO Input",
                              delegate=lambda: self.OnAddLogicBlock.Invoke(InputLogicBlock(bool))), 0, 0)
        self.ioSection.AddElement(
            self.CreateButton("Images/numberIcon.png", "Number Input",
                              delegate=lambda: self.OnAddLogicBlock.Invoke(InputLogicBlock(float))), 1, 0)
        self.ioSection.AddElement(
            self.CreateButton("Images/checkboxIcon.png", "YES/NO Output",
                              delegate=lambda: self.OnAddLogicBlock.Invoke(OutputLogicBlock(bool))), 0, 1)
        self.ioSection.AddElement(
            self.CreateButton("Images/numberIcon.png", "Number Output",
                              delegate=lambda: self.OnAddLogicBlock.Invoke(OutputLogicBlock(float))), 1, 1)

        self.annotationSection = ToolbarSection("Other")
        self.annotationSection.AddElement(
            self.CreateButton("Images/imageIcon.png", "Image", above=True, delegate=self.BrowseForImage), 0, 0, 2, 1)

        self.proceduresSection = ToolbarSection("Procedures")

        proceduresWidget = QFrame()
        proceduresWidgetLayout = QHBoxLayout()
        proceduresWidgetLayout.setContentsMargins(0, 0, 0, 0)
        proceduresWidgetLayout.setSpacing(0)
        proceduresWidget.setLayout(proceduresWidgetLayout)
        self.procedureSelectionBox = ProcedureSelectionBox()
        self.procedureSelectionBox.setToolTip("Procedure Selection")
        self.procedureSelectionBox.installEventFilter(self)
        self.procedureSelectionBox.OnProcedureSelected.Register(self.OnProcedureSelected.Invoke)
        self.playButton = self.CreateButton("Images/playIcon.png", "Run Procedure",
                                            delegate=self.OnProcedurePlay.Invoke, trueColor=True,
                                            showText=False)
        self.stopButton = self.CreateButton("Images/stopIcon.png", "Stop Procedure",
                                            delegate=self.OnProcedureStop.Invoke, trueColor=True,
                                            showText=False)
        self.addButton = self.CreateButton("Images/plusIcon.png", "New Procedure",
                                           delegate=self.PromptNewProcedure,
                                           showText=False)

        proceduresWidgetLayout.addWidget(self.playButton)
        proceduresWidgetLayout.addWidget(self.stopButton)
        proceduresWidgetLayout.addWidget(self.procedureSelectionBox)
        proceduresWidgetLayout.addWidget(self.addButton)

        self.proceduresSection.AddElement(proceduresWidget, 0, 0)

        self.proceduresSection.AddElement(
            self.CreateButton("Images/listIcon.png", "Manage...", delegate=self.OnManageProcedures.Invoke), 1, 0)

        self.solenoidsSection = ToolbarSection("Rig")
        self.solenoidsSection.AddElement(
            self.CreateButton("Images/solenoidsIcon.png", "Open Rig...", above=True,
                              delegate=self.OnOpenRig.Invoke), 0, 0, 2, 1)

        sections = [self.fileMenuSection,
                    self.logicBlocksSection,
                    self.chipSection,
                    self.procedureElementsSection,
                    self.ioSection,
                    self.proceduresSection,
                    self.annotationSection,
                    self.solenoidsSection]

        currentColumn = 0
        for section in sections:
            currentColumn = section.AddToGridLayout(layout, currentColumn)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    STATE_CHIP_EDIT = 1
    STATE_PROCEDURE_EDIT = 2
    STATE_LB_EDIT = 4

    def SetState(self, state):
        self.setUpdatesEnabled(False)
        self.chipSection.SetVisible(False)
        self.procedureElementsSection.SetVisible(False)
        self.ioSection.SetVisible(False)
        self.chipSection.SetVisible(state == MainToolbar.STATE_CHIP_EDIT)
        self.procedureElementsSection.SetVisible(state == MainToolbar.STATE_PROCEDURE_EDIT)
        self.ioSection.SetVisible(state == MainToolbar.STATE_LB_EDIT)
        self.setUpdatesEnabled(True)

    def UpdateForProcedureStatus(self, isRunning):
        self.procedureSelectionBox.setEnabled(not isRunning)

        for b in self.buttons:
            if b == self.stopButton or b == self.playButton:
                continue
            b.setEnabled(not isRunning)

        self.stopButton.setVisible(isRunning)
        self.playButton.setVisible(not isRunning)

    def CreateButton(self, icon, text, delegate=None, menu=None, above=False, showText=True, trueColor=False):
        b = QToolButton()
        b.setToolTip(text)
        if showText:
            if above:
                b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            else:
                text = "   " + text
                b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            b.setText(text)
        else:
            b.setText("")

        if icon is not None:
            if trueColor:
                color = None
            else:
                color = QColor(230, 230, 230)
            b.setIcon(ColorIcon(icon, color))

        if delegate is not None:
            b.clicked.connect(delegate)
        b.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        if menu is not None:
            b.setPopupMode(QToolButton.InstantPopup)
            b.setMenu(menu)

        self.buttons.append(b)

        b.installEventFilter(self)

        return b

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(watched, QWidget):
            if event.type() == QEvent.Enter:
                StatusBar.globalStatusBar.SetInfoMessage(watched.toolTip())
            elif event.type() == QEvent.Leave:
                StatusBar.globalStatusBar.SetInfoMessage("")
        return False

    def LogicBlockMenu(self, blocks: typing.List[typing.Type[BaseConnectableBlock]]):
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
                name, extension = os.path.splitext(filename[0])
                if extension == '.ulb':
                    newBlock = CompoundLogicBlock.LoadFromFile(filename[0])
                elif extension == '.usb':
                    newBlock = ScriptedBlock(filename[0])
                else:
                    return
                self.OnAddLogicBlock.Invoke(newBlock)

    def BrowseForImage(self):
        dialog = BrowseForImageDialog(self)
        if dialog.exec_():
            filename = dialog.selectedFiles()

            if filename is not None:
                newImage = Image(filename[0])
                self.OnAddImage.Invoke(newImage)

    def SetChipController(self, chipController):
        self.getMenu.SetChipController(chipController)
        self.setMenu.SetChipController(chipController)
        self.procedureSelectionBox.SetChipController(chipController)

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
        self.setNameFilters(["μChip Block (*.ulb *.usb)", "μChip Logic Block (*.ulb)", 'μChip Scripted Block (*.usb)'])
