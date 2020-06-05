from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from UI.WorldBrowser.BlockItem import *
from LogicBlocks.CompoundLogicBlock import *


class ImageItem(BlockItem):
    def __init__(self, s: QGraphicsScene, image: Image):
        super().__init__()

        self.image = image

        self.pixmap: typing.Optional[QPixmap] = None

        self.imageWidget = QLabel()
        self.container.layout().addWidget(self.imageWidget)
        self.container.setStyleSheet(self.container.styleSheet() + "*[roundedFrame=true] {border-radius: 0px;}")
        self.setZValue(-20)

        self.scaleSlider = QFrame(self.imageWidget)
        self.scaleSlider.setStyleSheet("""
        * {
        background-color: white;
        color: black;
        }
        """)
        self.scaleSliderLayout = QHBoxLayout()
        self.scaleSlider.setLayout(self.scaleSliderLayout)
        self.scaleSliderLayout.addWidget(QLabel("Scale: "))
        self.spin = QDoubleSpinBox()
        self.spin.setSingleStep(0.1)
        self.spin.setValue(image.GetScale())
        self.scaleSliderLayout.addWidget(self.spin)
        self.spin.valueChanged.connect(self.image.SetScale)

        self.image.OnScaleChanged.Register(self.ReloadImage, True)
        self.image.OnDestroyed.Register(self.Destroy, True)

        s.addItem(self)
        self.ReloadImage()

    def Destroy(self):
        self.image.OnScaleChanged.Unregister(self.ReloadImage)
        self.image.OnDestroyed.Unregister(self.Destroy)
        self.deleteLater()

    def SetIsSelected(self, isSelected):
        super().SetIsSelected(isSelected)
        if isSelected:
            self.scaleSlider.setVisible(True)
        else:
            self.scaleSlider.setVisible(False)

    def ReloadImage(self):
        self.pixmap = QPixmap(self.image.filename)
        self.pixmap = self.pixmap.scaledToWidth(self.pixmap.width() * self.image.GetScale())
        self.imageWidget.setPixmap(self.pixmap)
        self.widget().setFixedSize(self.pixmap.size())
        self.scaleSlider.move(
            self.widget().rect().center() - QPoint(self.scaleSlider.width(), self.scaleSlider.height()) * 0.5)
        self.setPos(self.image.GetPosition() - self.MySize() * 0.5)

    def MySize(self):
        return QPointF(self.pixmap.width(), self.pixmap.height())

    def MoveFinished(self):
        self.image.SetPosition(self.scenePos() + self.MySize() * 0.5)

    def TryDelete(self):
        if super().TryDelete():
            self.image.Destroy()
            return True
        return False
