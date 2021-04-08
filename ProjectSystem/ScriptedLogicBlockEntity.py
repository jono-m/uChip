from BlockSystemEntity import BlockSystemEntity, BaseConnectableBlock
from BlockSystem.ScriptedLogicBlock import ScriptedLogicBlock
from ProjectSystem.ScriptedLogicBlockFile import ScriptedLogicBlockFile
from pathlib import Path
from FileTracker import FileTracker


class ScriptedLogicBlockFileTracker(FileTracker):
    def __init__(self, path: Path, block: ScriptedLogicBlock):
        self._scriptedLogicBlock = block
        super().__init__(path)

    def ReportError(self, error: str):
        super().ReportError(error)
        self._scriptedLogicBlock.SetInvalid(error)

    def GetScriptedLogicBlock(self):
        return self._scriptedLogicBlock

    def TryReload(self) -> bool:
        if not super().TryReload():
            return False
        try:
            newFile = ScriptedLogicBlockFile.LoadFromFile(self.pathToLoad)
        except Exception as e:
            self.ReportError("Could not open file. Error:\n" + str(e))
            return False
        try:
            self._scriptedLogicBlock.Execute(newFile.getNameScript,
                                             newFile.getPortsScript,
                                             newFile.getParametersScript,
                                             newFile.computeOutputsScript)
        except Exception as e:
            self.ReportError("Script loading error:\n" + str(e))
            return False
        return True

    def OnSyncedSuccessfully(self):
        super().OnSyncedSuccessfully()
        self._scriptedLogicBlock.SetValid()


class ScriptedLogicBlockEntity(BlockSystemEntity):
    def __init__(self, path: Path, block: ScriptedLogicBlock):
        super().__init__(block)

        self.editableProperties['scriptedBlockFile'] = ScriptedLogicBlockFileTracker(path, block)

    def GetBlock(self) -> BaseConnectableBlock:
        self.editableProperties['scriptedBlockFile'].Sync()
        return self.editableProperties['scriptedBlockFile'].GetScriptedLogicBlock()
