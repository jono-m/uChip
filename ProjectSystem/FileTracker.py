import typing
import os
from pathlib import Path


class FileTracker:
    def __init__(self, path: Path):
        self.pathToLoad: Path = path
        self._lastAttemptedLoadedPath: typing.Optional[Path] = None
        self._lastAttemptedLoadedVersion: float = -1

        self._errorMessage: typing.Optional[str] = ""

        self.Sync()

    def GetErrorMessage(self):
        return self._errorMessage

    def ReportError(self, error: str):
        self._errorMessage = error

    def __setstate__(self, state):
        self.Sync()

    # Makes sure that the latest version of pathToLoad has been loaded up
    def Sync(self):
        if self.ShouldReload():
            if self.TryReload():
                self.OnSyncedSuccessfully()

    def ShouldReload(self) -> bool:
        # If we don't have a good file yet, we should keep trying to reload
        if self._lastAttemptedLoadedPath is None or not self._lastAttemptedLoadedPath.exists():
            return True
        # If we are trying to load a new path, time to reload
        if self.pathToLoad != self._lastAttemptedLoadedPath:
            return True
        # If there is a newer version available, time to reload
        if os.path.getmtime(self.pathToLoad) > self._lastAttemptedLoadedVersion:
            return True

        # Business as usual
        return False

    # Try to reload from pathToLoad
    # Return true if successful, false otherwise
    def TryReload(self) -> bool:
        if not self.pathToLoad.exists():
            self.ReportError("Cannot find file " + str(self.pathToLoad.resolve()) + ".")

            # Couldn't find it. The path was invalid, so we didn't even make a true attempt to load it.
            self._lastAttemptedLoadedPath = None
            self._lastAttemptedLoadedVersion = -1
            return False
        else:
            # Path exists, so good from down here.
            self._lastAttemptedLoadedPath = self.pathToLoad
            self._lastAttemptedLoadedVersion = os.path.getmtime(self.pathToLoad)
            return True

    def OnSyncedSuccessfully(self):
        self._errorMessage = ""
