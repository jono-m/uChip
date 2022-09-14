import pathlib
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtCore import QPoint, Qt, QSize, QRectF

from UI.CustomGraphicsView import CustomGraphicsView
from UI.ChipViewItems import ValveItem, ImageItem, TextItem, ProgramItem
from UI.UIMaster import UIMaster
from Data.Chip import Valve, Image, Text, Program


class ChipView(QWidget):
    def __init__(self):
        super().__init__()
        self.graphicsView = CustomGraphicsView()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.layout().addWidget(self.graphicsView)

        self.toolPanel = QWidget(self)
        self.finishEditsButton = QPushButton()
        self.finishEditsButton.setFocusPolicy(Qt.NoFocus)
        self.finishEditsButton.setToolTip("Finish editing")
        self.finishEditsButton.setIcon(
            ColoredIcon("Assets/Images/checkIcon.png", QColor(100, 100, 100)))
        self.finishEditsButton.setFixedSize(50, 50)
        self.finishEditsButton.setIconSize(QSize(30, 30))
        self.finishEditsButton.clicked.connect(lambda: self.SetEditing(False))

        self.editButton = QPushButton()
        self.editButton.setFocusPolicy(Qt.NoFocus)
        self.editButton.setIcon(
            ColoredIcon("Assets/Images/Edit.png", QColor(100, 100, 100)))
        self.editButton.setToolTip("Edit chip")
        self.editButton.setFixedSize(50, 50)
        self.editButton.setIconSize(QSize(30, 30))
        self.editButton.clicked.connect(lambda: self.SetEditing(True))

        self.addValveButton = QPushButton()
        self.addValveButton.setFocusPolicy(Qt.NoFocus)
        self.addValveButton.setToolTip("Add valve")
        self.addValveButton.setIcon(
            ColoredIcon("Assets/Images/plusIcon.png", QColor(100, 100, 100)))
        self.addValveButton.setFixedSize(30, 30)
        self.addValveButton.setIconSize(QSize(20, 20))
        self.addValveButton.clicked.connect(self.AddNewValve)

        self.addImageButton = QPushButton()
        self.addImageButton.setFocusPolicy(Qt.NoFocus)
        self.addImageButton.setToolTip("Add image")
        self.addImageButton.setIcon(
            ColoredIcon("Assets/Images/plusIcon.png", QColor(100, 100, 100)))
        self.addImageButton.setFixedSize(30, 30)
        self.addImageButton.setIconSize(QSize(20, 20))
        self.addImageButton.clicked.connect(self.AddNewImage)

        self.addProgramButton = QPushButton()
        self.addProgramButton.setFocusPolicy(Qt.NoFocus)
        self.addProgramButton.setToolTip("Add program")
        self.addProgramButton.setIcon(
            ColoredIcon("Assets/Images/plusIcon.png", QColor(100, 100, 100)))
        self.addProgramButton.setFixedSize(30, 30)
        self.addProgramButton.setIconSize(QSize(20, 20))
        self.addProgramButton.clicked.connect(self.AddNewProgram)

        self.addTextButton = QPushButton()
        self.addTextButton.setFocusPolicy(Qt.NoFocus)
        self.addTextButton.setToolTip("Add text")
        self.addTextButton.setIcon(
            ColoredIcon("Assets/Images/plusIcon.png", QColor(100, 100, 100)))
        self.addTextButton.setFixedSize(30, 30)
        self.addTextButton.setIconSize(QSize(20, 20))
        self.addTextButton.clicked.connect(self.AddNewText)

        toolPanelLayout = QVBoxLayout()
        toolPanelLayout.setContentsMargins(0, 0, 0, 0)
        toolPanelLayout.setSpacing(0)
        self.toolPanel.setLayout(toolPanelLayout)

        toolPanelLayout.addWidget(self.finishEditsButton, alignment=Qt.AlignHCenter)
        toolPanelLayout.addWidget(self.editButton)

        self.toolOptions = QWidget()
        toolOptionsLayout = QVBoxLayout()
        toolOptionsLayout.addWidget(self.addValveButton, alignment=Qt.AlignHCenter)
        toolOptionsLayout.addWidget(self.addImageButton, alignment=Qt.AlignHCenter)
        toolOptionsLayout.addWidget(self.addTextButton, alignment=Qt.AlignHCenter)
        toolOptionsLayout.addWidget(self.addProgramButton, alignment=Qt.AlignHCenter)
        self.toolOptions.setLayout(toolOptionsLayout)
        toolPanelLayout.addWidget(self.toolOptions)

        self.SetEditing(True)

    def resizeEvent(self, event):
        self.UpdateToolPanelPosition()
        super().resizeEvent(event)

    def UpdateToolPanelPosition(self):
        r = self.rect()

        padding = 20
        self.toolPanel.adjustSize()
        self.toolPanel.move(r.topLeft() + QPoint(padding, padding))

    def SetEditing(self, isEditing: bool):
        self.graphicsView.SetInteractive(isEditing)
        self.editButton.setVisible(not isEditing)
        self.finishEditsButton.setVisible(isEditing)
        self.toolOptions.setVisible(isEditing)

        self.UpdateToolPanelPosition()

    def AddNewValve(self):
        highestValveNumber = max(
            [x.solenoidNumber for x in UIMaster.Instance().currentChip.valves] + [-1])
        newValve = Valve()
        newValve.name = "Valve " + str(highestValveNumber + 1)
        newValve.solenoidNumber = highestValveNumber + 1
        UIMaster.Instance().currentChip.valves.append(newValve)
        newValveItem = ValveItem.ValveItem(newValve)
        self.graphicsView.AddItems([newValveItem])
        self.graphicsView.CenterItem(newValveItem)
        self.graphicsView.SelectItems([newValveItem])

    def AddNewImage(self):
        path = ImageItem.ImageItem.Browse(self)
        if path:
            newImage = Image()
            newImage.path = path
            UIMaster.Instance().currentChip.images.append(newImage)
            newImageItem = ImageItem.ImageItem(newImage)
            newImageItem.SetRect(
                QRectF(newImageItem.GetRect().topLeft(),
                       QSize(newImageItem.qtImage.size())))
            self.graphicsView.AddItems([newImageItem])
            self.graphicsView.CenterItem(newImageItem)
            self.graphicsView.SelectItems([newImageItem])

    def AddNewText(self):
        newText = Text()
        newText.text = "New text"
        UIMaster.Instance().currentChip.text.append(newText)
        newTextItem = TextItem.TextItem(newText)
        self.graphicsView.AddItems([newTextItem])
        self.graphicsView.CenterItem(newTextItem)
        self.graphicsView.SelectItems([newTextItem])

    def AddNewProgram(self):
        path = ProgramItem.ProgramItem.Browse(self)
        if path:
            newProgram = Program()
            newProgram.path = pathlib.Path(path)
            newProgram.name = newProgram.path.stem
            UIMaster.Instance().currentChip.programs.append(newProgram)
            newProgramItem = ProgramItem.ProgramItem(newProgram)
            self.graphicsView.AddItems([newProgramItem])
            self.graphicsView.CenterItem(newProgramItem)
            self.graphicsView.SelectItems([newProgramItem])

    def CloseChip(self):
        self.graphicsView.Clear()

    def OpenChip(self):
        valveItems = [ValveItem.ValveItem(valve) for valve in
                      UIMaster.Instance().currentChip.valves]
        [v.SetRect(QRectF(*valve.rect)) for v, valve in
         zip(valveItems, UIMaster.Instance().currentChip.valves)]
        [v.valveWidget.setEnabled(not self.graphicsView.isInteractive) for v in valveItems]
        self.graphicsView.AddItems(valveItems)

        imageItems = [ImageItem.ImageItem(image) for image in
                      UIMaster.Instance().currentChip.images]
        self.graphicsView.AddItems(imageItems)

        textItems = [TextItem.TextItem(text) for text in UIMaster.Instance().currentChip.text]
        self.graphicsView.AddItems(textItems)

        programItems = [ProgramItem.ProgramItem(program) for program in
                        UIMaster.Instance().currentChip.programs]
        self.graphicsView.AddItems(programItems)


class ColoredIcon(QIcon):
    def __init__(self, filename, color: QColor):
        pixmap = QPixmap(filename)
        replaced = QPixmap(pixmap.size())
        replaced.fill(color)
        replaced.setMask(pixmap.createMaskFromColor(Qt.transparent))
        super().__init__(replaced)
