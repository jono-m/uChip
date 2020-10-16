from UI.LogicBlock.ImageItem import *
from UI.LogicBlock.LogicBlockItem import *
from UI.WorldBrowser.WorldBrowser import *


class LogicBlockEditor(QFrame):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.worldBrowser = WorldBrowser()
        layout.addWidget(self.worldBrowser)

        self.currentBlock: typing.Optional[CompoundLogicBlock] = None

        self.setLayout(layout)

    def Clear(self):
        if self.currentBlock is not None:
            self.currentBlock.OnBlockAdded.Unregister(self.CreateBlockItem)
            self.currentBlock.OnSubBlockConnected.Unregister(self.CreateConnectionItem)
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
            for outputPort in blockItem.blockWidget.block.GetOutputs():
                # To each input
                for inputPort in outputPort.connectedInputs:
                    self.CreateConnectionItem((outputPort, inputPort))

        for imageItem in self.currentBlock.GetImages():
            self.CreateImageItem(imageItem)

        self.worldBrowser.FrameItems()
        self.currentBlock.OnBlockAdded.Register(self.CreateBlockItem, True)
        self.currentBlock.OnSubBlockConnected.Register(self.CreateConnectionItem, True)
        self.currentBlock.OnImageAdded.Register(self.CreateImageItem, True)
        self.currentBlock.OnClosed.Register(self.Clear, True)

    def CreateBlockItem(self, newBlock: LogicBlock):
        if isinstance(newBlock, LogicBlock):
            return BlockItemGraphicsWidget(self.worldBrowser.scene(), LogicBlockItem(newBlock))

    def CreateImageItem(self, image: Image):
        return ImageItem(self.worldBrowser.scene(), image)

    def CreateConnectionItem(self, t: typing.Tuple[Port, Port]):
        blockItems = [blockItem for blockItem in self.worldBrowser.scene().items() if
                      isinstance(blockItem, LogicBlockItem)]

        foundOutputWidget: typing.Optional[OutputPortWidget] = None

        foundInputWidget: typing.Optional[InputPortWidget] = None

        for blockItem in blockItems:
            if foundOutputWidget is None and blockItem.block == t[0].block:
                outputWidgets = [x for x in blockItem.outputPortsListWidget.children() if
                                 isinstance(x, OutputPortWidget)]
                for outputWidget in outputWidgets:
                    if outputWidget.outputPort == t[0]:
                        foundOutputWidget = outputWidget
                        break
            if foundInputWidget is None and blockItem.block == t[1].block:
                inputWidgets = [x for x in blockItem.inputPortsListWidget.children() if isinstance(x, InputPortWidget)]
                for inputWidget in inputWidgets:
                    if inputWidget.inputPort == t[1]:
                        foundInputWidget = inputWidget
                        break

        if foundOutputWidget is not None and foundInputWidget is not None:
            newConnection = BlockConnection(self.worldBrowser.scene(), foundOutputWidget.portHole,
                                            foundInputWidget.portHole)
            return newConnection

    def UpdateFromSave(self):
        if self.currentBlock is None:
            return
        self.currentBlock.ReloadFileSubBlocks()
