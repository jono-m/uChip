from LogicBlocks.CompoundLogicBlock import *
from UI.WorldBrowser.BlockItem import *
from UI.StylesheetLoader import *


class ImageItem(BlockItem):
    def __init__(self, s: QGraphicsScene, image: Image):
        super().__init__()

        self.image = image

        self.rawPixmap: typing.Optional[QPixmap] = None
        self.scaledPixmap: typing.Optional[QPixmap] = None

        self.imageWidget = QLabel()
        self.container.layout().addWidget(self.imageWidget)
        self.setZValue(-20)

        self.image.OnScaleChanged.Register(self.RescaleImage, True)
        self.image.OnDestroyed.Register(self.Destroy, True)

        s.addItem(self)
        self.ReloadImage()
        self.RescaleImage()

    def Destroy(self):
        self.image.OnScaleChanged.Unregister(self.ReloadImage)
        self.image.OnDestroyed.Unregister(self.Destroy)
        self.deleteLater()

    def ReloadImage(self):
        self.rawPixmap = QPixmap(self.image.filename)

    def RescaleImage(self):
        self.scaledPixmap = self.rawPixmap.scaledToWidth(self.rawPixmap.width() * self.image.GetScale())
        self.imageWidget.setPixmap(self.scaledPixmap)
        self.widget().setFixedSize(self.scaledPixmap.size())
        self.setPos(self.image.GetPosition() - self.MySize() * 0.5)

    def MySize(self):
        return QPointF(self.scaledPixmap.width(), self.scaledPixmap.height())

    def MoveFinished(self):
        self.image.SetPosition(self.scenePos() + self.MySize() * 0.5)

    def TryDelete(self):
        if super().TryDelete():
            self.image.Destroy()
            return True
        return False

    def OnDoubleClick(self):
        super().OnDoubleClick()
        newWindow = ImageSizeDialog(parent=self.scene().views()[0].topLevelWidget(), image=self.image)
        newWindow.exec_()


class ImageSizeDialog(QDialog):
    def __init__(self, parent, image: Image):
        super().__init__(parent=parent, f=Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        self.setModal(True)

        self.image = image

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        StylesheetLoader.GetInstance().RegisterWidget(self)

        namePanel = QFrame()
        namePanel.setObjectName("listPanel")
        nameLayout = QHBoxLayout()
        nameLayout.setContentsMargins(0, 0, 0, 0)
        nameLayout.setSpacing(0)
        nameLayout.addWidget(QLabel("File: "))
        nameLayout.addWidget(QLabel(image.filename))
        namePanel.setLayout(nameLayout)

        scalePanel = QFrame()
        scalePanel.setObjectName("listPanel")
        scaleLayout = QHBoxLayout()
        scaleLayout.setContentsMargins(0, 0, 0, 0)
        scaleLayout.setSpacing(0)
        scaleLayout.addWidget(QLabel("Scale: "))
        self.spin = QDoubleSpinBox()
        self.spin.setSingleStep(0.1)
        self.spin.setValue(image.GetScale())
        self.spin.valueChanged.connect(self.image.SetScale)
        scaleLayout.addWidget(self.spin)
        scalePanel.setLayout(scaleLayout)

        layout.addWidget(namePanel)
        layout.addWidget(scalePanel)

        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        layout.addWidget(ok)

        self.setWindowTitle("Image Properties")
        self.show()

        print(self.spin.objectName())
