from ProjectEntity import ProjectEntity
from pathlib import Path
from PySide2.QtGui import QPixmap
import typing
import time
import os


class Image(ProjectEntity):
    def __init__(self, path: Path):
        super().__init__()
        self.editableProperties['imagePath'] = path
        self.editableProperties['scale'] = 1
        self.editableProperties['opacity'] = 1

        # Assume it hasn't been loaded yet
        self._rawPixmap: typing.Optional[QPixmap] = None
        self._scaledPixmap: typing.Optional[QPixmap] = None
        self._loadedPath: typing.Optional[Path] = None
        self._loadedVersion: typing.Optional[float] = None
        self._currentScale: typing.Optional[float] = None

        self._errorMessage = ""

    def GetImage(self) -> typing.Optional[QPixmap]:
        self.UpdateEntity()
        return self._scaledPixmap

    def UpdateEntity(self):
        path: Path = self.editableProperties['imagePath']
        if not path.exists():
            self._errorMessage = "Cannot find file " + str(path.resolve()) + "."
            self._loadedPath = None
            self._loadedVersion = None
            self._rawPixmap = None
            self._scaledPixmap = None
        elif self._loadedVersion is None or self._loadedPath != path or os.path.getmtime(path) > self._loadedVersion:
            try:
                self._scaledPixmap = None
                self._rawPixmap = QPixmap(str(path.resolve()))
            except Exception as e:
                self._errorMessage = "Could not load file " + str(path.resolve()) + ".\nError: " + str(e)
                self._rawPixmap = None

            self._loadedVersion = os.path.getmtime(path)
            self._loadedPath = path

        if self._scaledPixmap is None or self._currentScale is None \
                or self._currentScale != self.editableProperties['scale']:
            if self._rawPixmap is None:
                self._scaledPixmap = None
            else:
                self._scaledPixmap = self._rawPixmap.scaledToWidth(
                    self._rawPixmap * self.editableProperties['scale'])
            self._currentScale = self.editableProperties['scale']
