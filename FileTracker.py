from pathlib import Path
import os


class ProjectFile:
    def __init__(self):
        self.absoluteFilePath = None


class AssetFile:
    def __init__(self, projectFile: ProjectFile):
        self._projectFile = projectFile
        self._relativePath = None
        self._parentAbsolutePath = parentAbsolutePath

        self._lastModifiedTime = None

    def NewerFileAvailable(self):
        if self.GetAbsolutePath():
            currentModifiedTime = os.path.getmtime(self.GetAbsolutePath())
            if currentModifiedTime != self._lastModifiedTime:
                return True
        return False

    def RecordVersionLoaded(self):
        self._lastModifiedTime = os.path.getmtime(self.GetAbsolutePath())

    def GetAbsolutePath(self):
        if self._parentAbsolutePath and self._relativePath:
            return self._parentAbsolutePath / self._relativePath
        else:
            return None

    def SetRelativeFromAbsolute(self, absolutePath: Path):
        self._relativePath = os.path.relpath(absolutePath, self._parentAbsolutePath)
