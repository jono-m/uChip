from LogicBlocks.IOBlocks import *
import dill as pickle
from pathlib import Path
import os


class CompoundLogicBlock(LogicBlock):
    def __init__(self):
        super().__init__()
        self.relativePath = None
        self.absolutePath = None
        self._version = None  # Used to keep track of which version of this compound block is used in another block.

        self._subBlocks: typing.Set[LogicBlock] = set()
        self._images: typing.Set[Image] = set()

        self.OnBlockAdded = Event()
        self.OnBlockRemoved = Event()
        self.OnImageAdded = Event()
        self.OnImageRemoved = Event()
        self.OnBlockMoved = Event()
        self.OnSubBlockConnected = Event()
        self.OnModified = Event()
        self.OnSaved = Event()

        self.OnModified.Register(self.UpdateOutputs)

    def Destroy(self):
        if not self.isDestroyed:
            super().Destroy()
            for s in self._subBlocks.copy():
                s.Destroy()

    def Close(self):
        super().Destroy()
        for s in self._subBlocks.copy():
            s.Close()
        for i in self._images:
            i.Close()

    def AddImage(self, image: 'Image'):
        self._images.add(image)
        self.OnModified.Invoke()
        image.OnPropertyChange.Register(self.OnModified.Invoke)
        image.OnMoved.Register(self.OnModified.Invoke)
        image.OnDestroyed.Register(self.RemoveImage)
        self.OnImageAdded.Invoke(image)

    def RemoveImage(self, image: 'Image'):
        if image not in self._images:
            return
        self._images.remove(image)
        self.OnModified.Invoke()
        image.OnDestroyed.Unregister(self.RemoveImage)
        image.OnPropertyChange.Unregister(self.OnModified.Invoke)
        image.OnMoved.Unregister(self.OnModified.Invoke)
        self.OnImageRemoved.Invoke(image)

    def GetSubBlocks(self) -> typing.Set[LogicBlock]:
        return self._subBlocks.copy()

    def GetInputs(self):
        inputBlocks = [x for x in self._subBlocks if
                       isinstance(x, InputLogicBlock) and x.parentBlockInputPort in self._inputs]
        inputBlocks.sort(key=lambda x: x.GetPosition().y())
        return [x.parentBlockInputPort for x in inputBlocks]

    def GetOutputs(self):
        outputBlocks = [x for x in self._subBlocks if
                        isinstance(x, OutputLogicBlock) and x.parentBlockOutputPort in self._outputs]
        outputBlocks.sort(key=lambda x: x.GetPosition().y())
        return [x.parentBlockOutputPort for x in outputBlocks]

    def Save(self, filename=None):
        if filename is not None:
            self.absolutePath = filename
        self.UpdateRelativePaths()
        file = open(self.absolutePath, "wb")
        pickle.dump(self, file)
        file.close()
        self.OnSaved.Invoke()

    def CreatesLoop(self, compoundBlock: 'CompoundLogicBlock'):
        unexplored: typing.List[CompoundLogicBlock] = [compoundBlock]
        while len(unexplored) > 0:
            toExplore = unexplored.pop(0)
            # TODO: This is where the bug for reloading on save is -- the relativepath is always None...
            if toExplore.relativePath == self.relativePath:
                return True
            else:
                unexplored += [x for x in toExplore._subBlocks if isinstance(x, CompoundLogicBlock)]
        return False

    def RemoveLoops(self):
        # Figure out which one of my sub-blocks has a loop
        myCompoundBlocks = [x for x in self._subBlocks if isinstance(x, CompoundLogicBlock)]

        for compoundBlock in myCompoundBlocks:
            if self.CreatesLoop(compoundBlock):
                self.RemoveSubBlock(compoundBlock)

    def BridgeConnections(self, reloadedCompoundBlock: 'CompoundLogicBlock'):
        for oldInput in self._inputs:
            for newInput in reloadedCompoundBlock._inputs:
                if oldInput.name == newInput.name and isinstance(newInput.GetDefaultData(),
                                                                 type(oldInput.GetDefaultData())):
                    # Found a match. Connect the new input to the output of the old one
                    if oldInput.connectedOutput is not None:
                        LogicBlock.Connect(oldInput.connectedOutput, newInput)
                    # Copy over default values
                    newInput.SetDefaultData(oldInput.GetDefaultData())
                    break

        for oldOutput in self._outputs:
            for newOutput in reloadedCompoundBlock._outputs:
                if oldOutput.name == newOutput.name and newOutput.dataType == oldOutput.dataType:
                    # Each of the connected inputs needs to get their stuff from the new output
                    for inputPort in oldOutput.connectedInputs:
                        LogicBlock.Connect(newOutput, inputPort)
                    break

    def UpdateAbsolutePaths(self):
        myCompoundBlocks = [x for x in self._subBlocks if isinstance(x, CompoundLogicBlock)]

        for compoundBlock in myCompoundBlocks:
            if compoundBlock.relativePath is not None:
                compoundBlock.absolutePath = str((Path(self.absolutePath) / compoundBlock.relativePath).resolve())
                compoundBlock.UpdateAbsolutePaths()

        for image in self._images:
            image.absolutePath = str((Path(self.absolutePath) / image.relativePath).resolve())

    def UpdateRelativePaths(self):
        myCompoundBlocks = [x for x in self._subBlocks if isinstance(x, CompoundLogicBlock)]

        for compoundBlock in myCompoundBlocks:
            if compoundBlock.absolutePath is not None:
                compoundBlock.relativePath = os.path.relpath(compoundBlock.absolutePath, self.absolutePath)
                compoundBlock.UpdateRelativePaths()

        for image in self._images:
            image.relativePath = os.path.relpath(image.absolutePath, self.absolutePath)

    def ReloadFileSubBlocks(self):
        # Make sure to remove any loops that might have been created through other file weirdness...
        self.RemoveLoops()

        myCompoundBlocks = [x for x in self._subBlocks if isinstance(x, CompoundLogicBlock)]

        for compoundBlock in myCompoundBlocks:
            # Any compound logic blocks need to be reloaded from their files to make sure that changes have been
            # included
            if compoundBlock.relativePath is not None:
                if os.path.exists(compoundBlock.absolutePath):
                    # File is still there, is it more updated than this one?
                    if compoundBlock._version != os.path.getmtime(compoundBlock.absolutePath):
                        # Outdated. Reload it!
                        replacementBlock = compoundBlock.Duplicate()
                        compoundBlock.BridgeConnections(replacementBlock)
                        self.RemoveSubBlock(compoundBlock)
                    else:
                        # Up to date! Don't need to do anything.
                        pass
                else:
                    # Doesn't exist
                    # TODO: Display an error message
                    self.RemoveSubBlock(compoundBlock)

    @staticmethod
    def LoadFromFile(filename) -> typing.Optional['CompoundLogicBlock']:
        _version = os.path.getmtime(filename)
        if not os.path.exists(filename):
            return None
        file = open(filename, "rb")
        block: CompoundLogicBlock = pickle.load(file)
        block._version = _version
        file.close()
        block.absolutePath = filename
        block.UpdateAbsolutePaths()
        block.UpdateRelativePaths()
        block.ReloadFileSubBlocks()
        return block

    def Duplicate(self) -> 'CompoundLogicBlock':
        newB = CompoundLogicBlock.LoadFromFile(self.absolutePath)
        for i in range(len(self._inputs)):
            newB._inputs[i].SetDefaultData(self._inputs[i].GetDefaultData())
        newB.SetPosition(self.GetPosition())
        self.OnDuplicated.Invoke(newB)
        return newB

    def AddSubBlock(self, newBlock: 'LogicBlock'):
        if isinstance(newBlock, InputLogicBlock) or isinstance(newBlock, OutputLogicBlock):
            newBlock.SetParentBlock(self)

        self._subBlocks.add(newBlock)
        newBlock.OnPortsChanged.Register(self.OnModified.Invoke)
        newBlock.OnConnectionsChanged.Register(self.OnModified.Invoke)
        newBlock.OnDefaultChanged.Register(self.OnModified.Invoke)
        newBlock.OnRefresh.Register(self.OnSubBlockConnected.Invoke)
        newBlock.OnDestroyed.Register(self.RemoveSubBlock)
        newBlock.OnMoved.Register(self.OnModified.Invoke)
        newBlock.OnDuplicated.Register(self.AddSubBlock)
        self.OnBlockAdded.Invoke(newBlock)
        self.OnModified.Invoke()

    def RemoveSubBlock(self, block: 'LogicBlock'):
        if block not in self._subBlocks:
            return
        self._subBlocks.remove(block)
        block.OnPortsChanged.Unregister(self.OnModified.Invoke)
        block.OnConnectionsChanged.Unregister(self.OnModified.Invoke)
        block.OnDefaultChanged.Unregister(self.OnModified.Invoke)
        block.OnRefresh.Unregister(self.OnSubBlockConnected.Invoke)
        block.OnDuplicated.Unregister(self.AddSubBlock)
        block.OnDestroyed.Unregister(self.RemoveSubBlock)
        block.OnMoved.Unregister(self.OnModified.Invoke)
        self.OnBlockRemoved.Invoke(block)
        self.OnModified.Invoke()

    def GetName(self=None):
        if self is None or self.absolutePath is None:
            return "New Logic Block"
        else:
            name, extension = os.path.splitext(os.path.basename(self.absolutePath))
            return name

    def UpdateOutputs(self):
        unExecuted = self.GetSubBlocks()
        while len(unExecuted) > 0:
            executable = [x for x in unExecuted if CompoundLogicBlock.IsExecutable(x, unExecuted)]
            for block in executable:
                unExecuted.remove(block)
                block.UpdateOutputs()
        super().UpdateOutputs()

    @staticmethod
    def IsExecutable(block: LogicBlock, unExecuted: typing.Set[LogicBlock]):
        parentBlocks = block.GetParentBlocks()
        if len(parentBlocks.intersection(unExecuted)) > 0:
            return False
        return True

    def GetImages(self):
        return self._images.copy()


class Image:
    def __init__(self, absolutePath: str):
        self._position = QPointF(0, 0)
        self.absolutePath = absolutePath
        self.relativePath = None
        self._scale = 1
        self._opacity = 1

        self.OnPropertyChange = Event()
        self.OnMoved = Event()
        self.OnDestroyed = Event()
        self.OnClosed = Event()

    def SetOpacity(self, opacity: float):
        self._opacity = opacity
        self.OnPropertyChange.Invoke()

    def SetPosition(self, position: QPointF):
        self._position = position
        self.OnMoved.Invoke()

    def SetScale(self, scale):
        self._scale = scale
        self.OnPropertyChange.Invoke()

    def Destroy(self):
        self.OnDestroyed.Invoke(self)

    def Close(self):
        self.OnClosed.Invoke(self)

    def GetPosition(self):
        return self._position

    def GetScale(self):
        return self._scale

    def GetOpacity(self):
        return self._opacity
