from UI.WorldBrowser.BlockItem import *
from UI.LogicBlock.BlockConnection import *
from Util import *


class LogicBlockItem(BlockItem):
    def __init__(self, scene: QGraphicsScene, b: LogicBlock, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.block = b

        self.titleBar = QLabel(self.block.GetName())
        self.titleBar.setContentsMargins(10, 5, 10, 5)

        titleLayout = QHBoxLayout()
        titleLayout.addWidget(self.titleBar, stretch=1)

        self.minMaxButton = QPushButton("-")
        self.minMaxButton.setStyleSheet("""
        QPushButton {
            background-color: rgba(0, 0, 0, 0);
            border: none;
            border-radius: 0px 8px 0px 0px;
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 0.2);
        }
        QPushButton:pressed {
            background-color: rgba(255, 255, 255, 0.3);
        }
        """)
        self.minMaxButton.setFixedWidth(25)
        self.minMaxButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.minMaxButton.clicked.connect(lambda checked=False: self.SetMinMax(not self.block.minimized))
        titleLayout.addWidget(self.minMaxButton, stretch=0)
        self.container.layout().addLayout(titleLayout)

        portsLayout = QHBoxLayout()
        portsLayout.setContentsMargins(0, 0, 0, 0)
        portsLayout.setSpacing(0)
        self.container.layout().addLayout(portsLayout)
        self.inputsWidget = QFrame()
        self.inputsWidget.setProperty('iWid', True)
        self.inputsWidget.setStyleSheet("""
        *[iWid=true] {
        border: 1px solid rgba(0, 0, 0, 0.2);
        border-width: 1px 0px 1px 0px;
        }""")
        self.inputsLayout = QVBoxLayout()
        self.inputsLayout.setAlignment(Qt.AlignTop)
        self.inputsWidget.setLayout(self.inputsLayout)
        portsLayout.addWidget(self.inputsWidget)
        for inputPort in self.block.GetInputs():
            inputWidget = InputWidget(inputPort, self)
            self.inputsLayout.addWidget(inputWidget)
        self.outputsWidget = QFrame()
        self.outputsWidget.setStyleSheet("""
        * {
        background-color: rgba(0, 0, 0, 0.2);
        }
        """)
        self.outputsLayout = QVBoxLayout()
        self.outputsLayout.setAlignment(Qt.AlignTop)
        self.outputsWidget.setLayout(self.outputsLayout)

        for outputPort in self.block.GetOutputs():
            outputWidget = OutputWidget(outputPort, self)
            self.outputsLayout.addWidget(outputWidget)
        portsLayout.addWidget(self.outputsWidget)

        scene.addItem(self)
        QApplication.processEvents()
        self.UpdatePos()

        self.block.OnPortsChanged.Register(self.UpdatePorts, True)
        self.block.OnDestroyed.Register(self.Destroy, True)
        self.block.OnMoved.Register(self.UpdatePos, True)
        self.block.OnOutputsUpdated.Register(self.UpdateName, True)

        self.SetMinMax(self.block.minimized)

    def SetMinMax(self, minimized):
        self.block.minimized = minimized
        if minimized:
            self.minMaxButton.setText("+")
        else:
            self.minMaxButton.setText("-")

        for inputItem in self.inputsWidget.children():
            if isinstance(inputItem, InputWidget):
                if not inputItem.inputPort.isConnectable:
                    inputItem.setVisible(not minimized)

    def UpdatePos(self):
        self.setPos(self.block.GetPosition() - self.rect().center())

    def Destroy(self):
        self.block.OnDestroyed.Unregister(self.Destroy)
        self.block.OnPortsChanged.Unregister(self.UpdatePorts)
        self.block.OnMoved.Unregister(self.UpdatePos)
        self.block.OnOutputsUpdated.Unregister(self.UpdateName)
        self.deleteLater()

    def UpdateName(self):
        self.titleBar.setText(self.block.GetName())
        self.inputsWidget.adjustSize()
        self.outputsWidget.adjustSize()
        self.container.adjustSize()
        self.widget().adjustSize()
        self.adjustSize()

    def UpdatePorts(self):
        hasNonConnectable = False

        inputPorts = [inputWidget.inputPort for inputWidget in self.inputsWidget.children() if
                      isinstance(inputWidget, InputWidget)]
        for inputPort in self.block.GetInputs():
            if not inputPort.isConnectable:
                hasNonConnectable = True
            if inputPort not in inputPorts:
                inputWidget = InputWidget(inputPort, self)
                self.inputsLayout.addWidget(inputWidget)

        outputPorts = [outputWidget.outputPort for outputWidget in self.outputsWidget.children() if
                       isinstance(outputWidget, OutputWidget)]
        for outputPort in self.block.GetOutputs():
            if outputPort not in outputPorts:
                outputWidget = OutputWidget(outputPort, self)
                self.inputsLayout.addWidget(outputWidget)

        hasInputs = len(self.block.GetInputs()) > 0
        hasOutputs = len(self.block.GetOutputs()) > 0
        self.outputsWidget.setVisible(hasOutputs)
        self.inputsWidget.setVisible(hasInputs)

        self.minMaxButton.setVisible(hasNonConnectable)

    def MoveFinished(self):
        self.block.SetPosition(self.scenePos() + self.rect().center())
        super().MoveFinished()

    def TryDelete(self):
        if super().TryDelete():
            self.block.Destroy()
            return True
        return False

    def TryDuplicate(self):
        copyBlock = self.block.Duplicate()
        copyBlock.SetPosition(self.block.GetPosition() + QPointF(30, 30))


class InputWidget(QFrame):
    def __init__(self, inputPort: InputPort, graphicsParent: QGraphicsProxyWidget):
        super().__init__()

        self.graphicsParent = graphicsParent

        self.setProperty('isMe', True)
        self.setStyleSheet("*[isMe=true]{border: none; background-color: transparent;}")

        self.inputPort = inputPort

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

        if self.inputPort.isConnectable and not (
                isinstance(self.graphicsParent.block, InputLogicBlock) or isinstance(self.graphicsParent.block,
                                                                                     OutputLogicBlock)):
            self.portHole = InputPortHole(inputPort, graphicsParent)
            layout.addWidget(self.portHole)

            self.nameText = QLabel()
            self.nameText.setStyleSheet("*{background-color: transparent}")
            layout.addWidget(self.nameText)

        self.parameterSetting = ParameterWidget(self.inputPort.dataType)
        self.parameterSetting.OnParameterChanged.Register(self.OnParameterChanged, True)
        layout.addWidget(self.parameterSetting)

        self.Update()

        self.inputPort.block.OnConnectionsChanged.Register(self.Update, True)
        self.inputPort.block.OnPortsChanged.Register(self.Update, True)
        self.inputPort.block.OnOutputsUpdated.Register(self.Update, True)
        self.inputPort.block.OnDestroyed.Register(self.Remove, True)

        self.Update()

    def Remove(self):
        self.inputPort.block.OnConnectionsChanged.Unregister(self.Update)
        self.inputPort.block.OnPortsChanged.Unregister(self.Update)
        self.inputPort.block.OnOutputsUpdated.Unregister(self.Update)
        self.inputPort.block.OnDestroyed.Unregister(self.Remove)
        self.deleteLater()

    def OnParameterChanged(self, data):
        self.inputPort.SetDefaultData(data)

    def Update(self):
        if self.inputPort not in self.inputPort.block.GetInputs():
            self.Remove()
            return

        self.parameterSetting.Update(self.inputPort.name, self.inputPort.GetDefaultData())

        if self.inputPort.isConnectable and not (
                isinstance(self.graphicsParent.block, InputLogicBlock) or isinstance(self.graphicsParent.block,
                                                                                     OutputLogicBlock)):
            if self.inputPort.connectedOutput is not None:
                self.portHole.SetIsFilled(True)
                self.nameText.setVisible(True)
                self.parameterSetting.setVisible(False)
            else:
                self.portHole.SetIsFilled(False)
                self.nameText.setVisible(False)
                self.parameterSetting.setVisible(True)
            if self.inputPort.dataType is float:
                dataText = "{:0.2f}".format(self.inputPort.GetData())
            else:
                dataText = str(self.inputPort.GetData())
            self.nameText.setText(self.inputPort.name + "<br>" + dataText)


class OutputWidget(QFrame):
    def __init__(self, outputPort: OutputPort, graphicsParent: QGraphicsProxyWidget):
        super().__init__()

        self.setProperty('isMe', True)
        self.setStyleSheet("*[isMe=true]{border: none; background-color: transparent;}")

        self.outputPort = outputPort

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignLeft)
        self.setLayout(layout)

        self.nameText = QLabel()
        self.nameText.setStyleSheet("*{background-color: transparent}")
        layout.addWidget(self.nameText)

        self.portHole = OutputPortHole(outputPort, graphicsParent)
        layout.addWidget(self.portHole)

        self.Update()

        self.outputPort.block.OnConnectionsChanged.Register(self.Update, True)
        self.outputPort.block.OnPortsChanged.Register(self.Update, True)
        self.outputPort.block.OnOutputsUpdated.Register(self.Update, True)
        self.outputPort.block.OnDestroyed.Register(self.Remove, True)

        self.Update()

    def Remove(self):
        self.outputPort.block.OnConnectionsChanged.Unregister(self.Update)
        self.outputPort.block.OnPortsChanged.Unregister(self.Update)
        self.outputPort.block.OnOutputsUpdated.Unregister(self.Update)
        self.outputPort.block.OnDestroyed.Unregister(self.Remove)
        self.deleteLater()

    def Update(self):
        if self.outputPort not in self.outputPort.block.GetOutputs():
            self.Remove()
            return

        if len(self.outputPort.connectedInputs) > 0:
            self.portHole.SetIsFilled(True)
        else:
            self.portHole.SetIsFilled(False)

        if self.outputPort.dataType is float:
            dataText = "{:0.2f}".format(self.outputPort.GetData())
        else:
            dataText = str(self.outputPort.GetData())
        self.nameText.setText(self.outputPort.name + "<br>" + dataText)


class ParameterWidget(QFrame):
    def __init__(self, dataType):
        super().__init__()

        self.dataType = dataType

        self.OnParameterChanged = Event()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.nameLabel = QLabel()
        layout.addWidget(self.nameLabel)
        if self.dataType == bool:
            self.control = QCheckBox()
            self.control.stateChanged.connect(self.ParameterChanged)
            self.nameLabel.setVisible(False)
            layout.addWidget(self.control)
        elif self.dataType == float or self.dataType is None:
            self.control = CleanSpinBox()
            self.control.wheelEvent = lambda event: None
            self.control.setKeyboardTracking(False)
            self.control.setRange(-(2 ** 24), 2 ** 24)
            self.control.valueChanged.connect(self.ParameterChanged)
            layout.addWidget(self.control)
        elif self.dataType == str:
            self.control = QLineEdit()
            self.control.setMaxLength(20)
            self.control.textChanged.connect(self.ParameterChanged)
            layout.addWidget(self.control)
        elif self.dataType == int:
            self.control = QSpinBox()
            self.control.wheelEvent = lambda event: None
            self.control.setKeyboardTracking(False)
            self.control.setRange(-2 ** 24, 2 ** 24)
            self.control.valueChanged.connect(self.ParameterChanged)
            layout.addWidget(self.control)
        else:
            return

        layout.addWidget(self.control)

    def Update(self, newName, newValue):
        self.control.blockSignals(True)
        if isinstance(self.control, QCheckBox):
            if self.control.isChecked() != newValue:
                self.control.setChecked(newValue)
            self.control.setText(newName)

        self.nameLabel.setText(newName)

        if isinstance(self.control, CleanSpinBox) or isinstance(self.control, QSpinBox):
            if self.control.value() != newValue:
                self.control.setValue(newValue)
        elif isinstance(self.control, QLineEdit):
            if self.control.text() != newValue:
                self.control.setText(newValue)
        self.control.blockSignals(False)

    def ParameterChanged(self, newParam):
        if self.dataType == bool:
            if newParam == Qt.CheckState.Checked:
                self.OnParameterChanged.Invoke(True)
            else:
                self.OnParameterChanged.Invoke(False)
        elif self.dataType == float or self.dataType == int or self.dataType == str or self.dataType is None:
            self.OnParameterChanged.Invoke(newParam)
