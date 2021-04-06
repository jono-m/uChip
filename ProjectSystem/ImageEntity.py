from ProjectEntity import ProjectEntity
from pathlib import Path
from PySide2.QtGui import QPixmap
from FileTrackingObject import FileTrackingObject
import typing


class ImageFileObject(FileTrackingObject):
    def __init__(self, path: Path):
        self._image: typing.Optional[QPixmap] = None
        super().__init__(path)

    def __getstate__(self):
        self._image = None
        return self.__dict__

    def GetImage(self):
        return self._image

    def ShouldReload(self) -> bool:
        return super().ShouldReload() or self._image is None

    def ReportError(self, error: str):
        super().ReportError(error)
        self._image = None

    def TryReload(self) -> bool:
        if not super().TryReload():
            return False
        try:
            self._image = QPixmap(str(self.pathToLoad.resolve()))
        except Exception as e:
            self.ReportError("Error loading file:\n" + str(e))
            return False
        return True


class Image(ProjectEntity):
    def __init__(self, path: Path):
        super().__init__()
        self.editableProperties['imageFile'] = ImageFileObject(path)
        self.editableProperties['scale'] = 1
        self.editableProperties['opacity'] = 1

        self._scaledPixmap: typing.Optional[QPixmap] = None
        self._currentScale: float = -1

    def __getstate__(self):
        self._scaledPixmap = None
        return self.__dict__

    def GetImage(self) -> typing.Optional[QPixmap]:
        self.editableProperties['imageFile'].Sync()

        image: QPixmap = self.editableProperties['imageFile'].GetImage()
        # Update the scaled version
        if image is None:
            self._scaledPixmap = None
        elif self._scaledPixmap is None or self._currentScale != self.editableProperties['scale']:
            self._scaledPixmap = image.scaledToWidth(image * self.editableProperties['scale'])
            self._currentScale = self.editableProperties['scale']

        return self._scaledPixmap
