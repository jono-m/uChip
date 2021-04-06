from BlockSystemEntity import BlockSystemEntity, BaseConnectableBlock
from BlockSystem.ScriptedLogicBlock import ScriptedLogicBlock
from pathlib import Path
from FileTrackingObject import FileTrackingObject


class ScriptedLogicBlockFile(FileTrackingObject):
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
            f = open(self.pathToLoad)
            code = f.read()
            f.close()
        except Exception as e:
            self.ReportError("Could not open file. Error:\n" + str(e))
            return False
        try:
            self._scriptedLogicBlock.ParseCode(code)
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

        self.editableProperties['scriptedBlockFile'] = ScriptedLogicBlockFile(path, block)

    def GetBlock(self) -> BaseConnectableBlock:
        self.editableProperties['scriptedBlockFile'].Sync()
        return self.editableProperties['scriptedBlockFile'].GetScriptedLogicBlock()
