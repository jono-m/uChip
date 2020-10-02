from UI.LogicBlock.LogicBlockItem import *
from ChipController.ValveBlock import *


class ValveBlockItem(LogicBlockItem):
    def __init__(self, s: QGraphicsScene, vb: ValveLogicBlock):
        super().__init__(s, vb)
        self.vb = vb
        self.container.setStyleSheet(self.container.styleSheet() + """
            *[valveState=true] {
                background-color: rgba(160, 191, 101, 1);
            }
            *[valveState=false] {
                background-color: rgba(191, 99, 103, 1);
            }
        """)
        self.container.setProperty("valveState", self.vb.IsOpen())
        self.container.setStyle(self.container.style())

        self.vb.OnOutputsUpdated.Register(self.ChangeColor, True)

        self.container.layout().removeWidget(self.titleBar)
        titleLayout = QHBoxLayout()
        titleLayout.addWidget(self.titleBar, stretch=1)

        self.minmaxButton = QPushButton("-")
        self.minmaxButton.setStyleSheet("""
        QPushButton {
            background-color: rgba(0, 0, 0, 0);
        }
        QPushButton:hover {
            background-color: rgba(0, 0, 0, 0.2);
        }
        QPushButton:pressed {
            background-color: rgba(0, 0, 0, 0.3);
        }
        """)
        self.minmaxButton.setFixedWidth(self.titleBar.height())
        self.minmaxButton.clicked.connect(lambda checked=False: self.SetMinMax(not self.vb.minimized))
        titleLayout.addWidget(self.minmaxButton, stretch=0)
        self.container.layout().insertLayout(0, titleLayout)

        self.SetMinMax(self.vb.minimized)

    def SetMinMax(self, minimized):
        self.vb.minimized = minimized
        if minimized:
            self.minmaxButton.setText("+")
        else:
            self.minmaxButton.setText("-")

        self.inputsWidget.setVisible(not minimized)
        self.outputsWidget.setVisible(not minimized)

        self.container.adjustSize()
        self.widget().adjustSize()

    def ChangeColor(self):
        lastStyle = self.container.property("valveState")
        if lastStyle != self.vb.IsOpen():
            self.container.setProperty("valveState", self.vb.IsOpen())
            self.container.setStyle(self.container.style())
