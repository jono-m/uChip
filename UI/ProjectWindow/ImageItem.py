from GraphSystem.Blocks.CompoundLogicBlock import *
from UI.ProjectWindow.GraphicalProjectEntity import *
from UI.StylesheetLoader import *


class ImageWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.opacity = 1

    def paintEvent(self, arg__1: QPaintEvent):
        painter = QPainter()
        painter.begin(self)
        painter.setOpacity(self.opacity)
        painter.drawPixmap(0, 0, self.pixmap())


class ImageItem(GraphicalProjectEntity):
    def __init__(self, s: QGraphicsScene, image: Image):
        super().__init__(s)

        self.container.setProperty("IsImage", True)
        self.image = image

        self.rawPixmap: typing.Optional[QPixmap] = None
        self.scaledPixmap: typing.Optional[QPixmap] = None

        self.imageWidget = ImageWidget()
        self.container.layout().addWidget(self.imageWidget)
        self.setZValue(-20)

        self.image.OnPropertyChange.Register(self.RescaleImage, True)
        self.image.OnDestroyed.Register(self.Destroy, True)

        s.addItem(self)
        self.ReloadImage()
        self.RescaleImage()

    def Destroy(self):
        self.image.OnPropertyChange.Unregister(self.ReloadImage)
        self.image.OnDestroyed.Unregister(self.Destroy)
        self.deleteLater()

    def ReloadImage(self):
        if not os.path.exists(self.image.absolutePath):
            self.rawPixmap = None
        else:
            self.rawPixmap = QPixmap(self.image.absolutePath)

    def RescaleImage(self):
        if self.rawPixmap is None:
            errorImage = QImage(256, 256, QImage.Format_RGB16)
            errorImage.fill(Qt.red)
            painter = QPainter()
            painter.begin(errorImage)
            painter.setPen(Qt.white)
            painter.setFont(QFont("sans-serif", 12, QFont.Bold))
            painter.drawText(errorImage.rect(), Qt.AlignCenter, "Image not found.")
            painter.end()
            self.scaledPixmap = QPixmap(errorImage)
        else:
            self.scaledPixmap = self.rawPixmap.scaledToWidth(self.rawPixmap.width() * self.image.GetScale())
        self.imageWidget.opacity = self.image.GetOpacity()
        self.imageWidget.setPixmap(self.scaledPixmap)
        self.widget().setFixedSize(self.scaledPixmap.size())
        self.setPos(self.image.GetPosition() - self.MySize() * 0.5)

    def MySize(self):
        return QPointF(self.scaledPixmap.width(), self.scaledPixmap.height())

    def MoveFinished(self):
        self.image.SetPosition(self.scenePos() + self.MySize() * 0.5)

    def TryDelete(self):
        self.image.Destroy()
        return True

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
        nameLayout = QHBoxLayout()
        nameLayout.setContentsMargins(0, 0, 0, 0)
        nameLayout.setSpacing(0)
        nameLayout.addWidget(QLabel("File: "))
        nameLayout.addWidget(QLabel("<i>" + image.absolutePath + "</i>"))
        namePanel.setLayout(nameLayout)

        scalePanel = QFrame()
        scaleLayout = QHBoxLayout()
        scaleLayout.setContentsMargins(0, 0, 0, 0)
        scaleLayout.setSpacing(0)
        scaleLayout.addWidget(QLabel("Scale: "), stretch=0)
        self.spin = QDoubleSpinBox()
        self.spin.setSingleStep(0.1)
        self.spin.setValue(image.GetScale())
        self.spin.valueChanged.connect(self.image.SetScale)
        scaleLayout.addWidget(self.spin, stretch=1)
        scalePanel.setLayout(scaleLayout)

        opacityPanel = QFrame()
        opacityLayout = QHBoxLayout()
        opacityLayout.setContentsMargins(0, 0, 0, 0)
        opacityLayout.setSpacing(0)
        opacityLayout.addWidget(QLabel("Opacity: "), stretch=0)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setTickInterval(10)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setValue(image.GetOpacity()*100)
        self.slider.valueChanged.connect(lambda x: self.image.SetOpacity(float(x)/100))
        opacityLayout.addWidget(self.slider, stretch=1)
        opacityPanel.setLayout(opacityLayout)

        layout.addWidget(namePanel)
        layout.addWidget(scalePanel)
        layout.addWidget(opacityPanel)

        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        layout.addWidget(ok)

        self.setWindowTitle("Image Properties")
        self.show()
        self.setFixedSize(self.size())
