import dill
import typing
from pathlib import Path


class ScriptedLogicBlockFileError(Exception):
    pass


class ScriptedLogicBlockFile:
    def __init__(self):
        self.getNameScript: str = "return \"New Scripted Logic Block\""
        self.getPortsScript: str = "return {}"
        self.getParametersScript: str = "return {}"
        self.computeOutputsScript: str = "return {}"

        self._filePath: typing.Optional[Path] = None

    def Save(self, path: Path):
        lastPath = self._filePath

        self._filePath = path

        try:
            file = open(self._filePath, "wb")
            dill.dump(self, file)
            file.close()
        except Exception as e:
            self._filePath = lastPath
            raise ScriptedLogicBlockFileError("Could not save file to " + str(path.resolve()) + ".\nError:" + str(e))

    @staticmethod
    def LoadFromFile(path: Path) -> 'ScriptedLogicBlockFile':
        if not path.exists():
            raise ScriptedLogicBlockFileError("Could not find file " + str(path.resolve()) + ".")

        try:
            file = open(path, "rb")
            loadedScriptedLogicBlock: 'ScriptedLogicBlockFile' = dill.load(file)
            file.close()
        except Exception as e:
            raise ScriptedLogicBlockFileError("Could not load file " + str(path.resolve()) + ".\nError:" + str(e))

        loadedScriptedLogicBlock._projectPath = path

        return loadedScriptedLogicBlock
