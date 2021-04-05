from BlockSystemEntity import BlockSystemEntity
from BlockSystem.ScriptedLogicBlock import ScriptedLogicBlock
from pathlib import Path
import os
import typing


class ScriptedLogicBlockEntity(BlockSystemEntity):
    def __init__(self, path: Path, block: ScriptedLogicBlock):
        super().__init__(block)

        # Assume it hasn't been loaded yet
        self.editableProperties['scriptedBlockPath'] = path
        self._attemptedLoadedPath: typing.Optional[Path] = None
        self._attemptedLoadedVersion: typing.Optional[float] = None

    def UpdateEntity(self):
        path: Path = self.editableProperties['scriptedBlockPath']
        block = self.GetBlock()
        if not isinstance(block, ScriptedLogicBlock):
            return

        if not path.exists():
            block.SetInvalid("Cannot find file " + str(path.resolve()) + ".")
            self._attemptedLoadedPath = None
            self._attemptedLoadedVersion = None
        elif self._attemptedLoadedVersion is None or path != self._attemptedLoadedPath or os.path.getmtime(
                path) > self._attemptedLoadedVersion:
            try:
                f = open(path)
                code = f.read()
                f.close()
            except Exception as e:
                block.SetInvalid("Could not read file " + str(path.resolve()) + ".\nError:" + str(e))
            else:
                try:
                    block.ParseCode(code)
                except Exception as e:
                    block.SetInvalid("Script loading error in " + str(path.resolve()) + ":\n" + str(e))
                else:
                    block.SetValid()

            self._attemptedLoadedVersion = os.path.getmtime(path)
            self._attemptedLoadedPath = path
