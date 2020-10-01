from UI.WorldBrowser.WorldBrowser import *
from LogicBlocks.CompoundLogicBlock import *
from UI.LogicBlock.BlockConnection import *
from UI.LogicBlock.ImageItem import *


class LogicBlockEditor(QFrame):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.worldBrowser = WorldBrowser()
        layout.addWidget(self.worldBrowser)

        self.currentBlock: typing.Optional[CompoundLogicBlock] = None

        self.worldBrowser.CanMakeConnectionFunc = self.CanConnectPorts
        self.worldBrowser.IsFromPortFunc = self.IsFromPort
        self.worldBrowser.OnMakeConnectionFunc = self.MakeConnection

        self.viewMapping: typing.List[typing.Tuple[typing.Type[LogicBlock], typing.Type[LogicBlockItem]]] = [
            (LogicBlock, LogicBlockItem)]

        self.setLayout(layout)

    def Clear(self):
        if self.currentBlock is not None:
            self.currentBlock.OnBlockAdded.Unregister(self.CreateBlockItem)
            self.currentBlock.OnSubBlockConnected.Unregister(self.CreateConnectionTuple)
            self.currentBlock.OnImageAdded.Unregister(self.CreateImageItem)
            self.currentBlock.OnClosed.Unregister(self.Clear)
        self.currentBlock = None

        self.worldBrowser.Clear()

    def LoadBlock(self, block: CompoundLogicBlock):
        self.Clear()
        self.currentBlock = block

        addedBlockItems = []
        for subBlock in self.currentBlock.GetSubBlocks():
            newBlockItem = self.CreateBlockItem(subBlock)
            if newBlockItem is not None:
                addedBlockItems.append(newBlockItem)

        # Go over each loaded block
        for blockItem in addedBlockItems:
            # Connect each output in the block
            for outputPort in blockItem.block.GetOutputs():
                # To each input
                for inputPort in outputPort.connectedInputs:
                    self.CreateConnectionItem(outputPort, inputPort)

        for imageItem in self.currentBlock.GetImages():
            self.CreateImageItem(imageItem)

        self.worldBrowser.FrameItems()
        self.currentBlock.OnBlockAdded.Register(self.CreateBlockItem, True)
        self.currentBlock.OnSubBlockConnected.Register(self.CreateConnectionTuple, True)
        self.currentBlock.OnImageAdded.Register(self.CreateImageItem, True)
        self.currentBlock.OnClosed.Register(self.Clear, True)

    def CreateBlockItem(self, newBlock: LogicBlock):
        for blockType, viewType in self.viewMapping:
            if isinstance(newBlock, blockType):
                newBlock = viewType(self.worldBrowser.scene(), newBlock)
                QApplication.processEvents()
                return newBlock

    def CreateImageItem(self, image: Image):
        return ImageItem(self.worldBrowser.scene(), image)

    def CreateConnectionTuple(self, t: typing.Tuple[OutputPort, InputPort]):
        return self.CreateConnectionItem(t[0], t[1])

    def CreateConnectionItem(self, outputPort: OutputPort, inputPort: InputPort):
        blockItems = [blockItem for blockItem in self.worldBrowser.scene().items() if
                      isinstance(blockItem, LogicBlockItem)]

        foundOutputWidget: typing.Optional[OutputWidget] = None

        foundInputWidget: typing.Optional[InputWidget] = None

        for blockItem in blockItems:
            if foundOutputWidget is None and blockItem.block == outputPort.block:
                outputWidgets = [x for x in blockItem.outputsWidget.children() if isinstance(x, OutputWidget)]
                for outputWidget in outputWidgets:
                    if outputWidget.outputPort == outputPort:
                        foundOutputWidget = outputWidget
                        break
            if foundInputWidget is None and blockItem.block == inputPort.block:
                inputWidgets = [x for x in blockItem.inputsWidget.children() if isinstance(x, InputWidget)]
                for inputWidget in inputWidgets:
                    if inputWidget.inputPort == inputPort:
                        foundInputWidget = inputWidget
                        break

        if foundOutputWidget is not None and foundInputWidget is not None:
            newConnection = BlockConnection(self.worldBrowser.scene(), foundOutputWidget, foundInputWidget)
            return newConnection

    def CanConnectPorts(self, fromPortHole: PortHoleWidget, toPortHole: PortHoleWidget):
        if not (isinstance(fromPortHole, OutputPortHole) and isinstance(toPortHole, InputPortHole)):
            return False

        return LogicBlock.CanConnect(fromPortHole.portWidget.outputPort, toPortHole.portWidget.inputPort)

    def IsFromPort(self, port: PortHoleWidget):
        if isinstance(port, OutputPortHole):
            return True
        return False

    def MakeConnection(self, fromPortHole: OutputPortHole, toPortHole: InputPortHole):
        block = fromPortHole.portWidget.outputPort.block
        block.Connect(fromPortHole.portWidget.outputPort, toPortHole.portWidget.inputPort)

    def UpdateFromSave(self):
        if self.currentBlock is None:
            return
        self.currentBlock.ReloadFileSubBlocks()


class BrowseForCustomDialog(QFileDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("Open a logic block")
        self.setFileMode(QFileDialog.ExistingFile)
        self.setAcceptMode(QFileDialog.AcceptOpen)
        self.setNameFilters(["μChip Logic Block (*.ulb)"])
