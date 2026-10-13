"""How an image is shown and edited.

On the canvas (ImageView) it is the image file stretched to the element's rect, reloaded when the file
changes, or a message if the file can't be loaded. In the inspector (ImageInspector) its path can be
typed or browsed for.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from backend.chip import Image
from gui.widgets import browse_for_image, sync_label, sync_line_edit


# Canvas

@dataclass(eq=False)
class ImageView:
    image: Image
    label: QLabel
    loaded: Optional[tuple] = None  # (path, modification time) of the shown image

    @property
    def widget(self) -> QWidget:
        return self.label

    def refresh(self):
        key = (self.image.path, _mtime(self.image.path))
        if key == self.loaded:
            return
        self.loaded = key
        pixmap = QPixmap(str(self.image.path))
        if pixmap.isNull():
            self.label.setPixmap(QPixmap())
            self.label.setText("Image not found:\n%s" % self.image.path)
            self.label.setFrameShape(QFrame.StyledPanel)
        else:
            self.label.setFrameShape(QFrame.NoFrame)
            self.label.setPixmap(pixmap)


def build_image_view(image: Image) -> ImageView:
    label = QLabel()
    label.setScaledContents(True)
    label.setAlignment(Qt.AlignCenter)
    label.setWordWrap(True)
    label.setMinimumSize(1, 1)
    label.setAttribute(Qt.WA_TranslucentBackground)
    return ImageView(image, label)


def _mtime(path: Path) -> Optional[float]:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


# Inspector

@dataclass(eq=False)
class ImageInspector:
    image: Image
    path: QLineEdit
    status: QLabel

    def refresh(self):
        sync_line_edit(self.path, str(self.image.path))
        sync_label(self.status, "" if self.image.path.exists() else "File not found.")


def build_image_inspector(image: Image, layout: QVBoxLayout) -> ImageInspector:
    inspector = ImageInspector(image, QLineEdit(), QLabel())
    inspector.status.setWordWrap(True)
    inspector.path.editingFinished.connect(lambda: setattr(image, "path", Path(inspector.path.text()).absolute()))

    def browse():
        path = browse_for_image(layout.parentWidget())
        if path is not None:
            image.path = path.absolute()

    browse_button = QPushButton("Browse...")
    browse_button.clicked.connect(browse)
    layout.addWidget(QLabel("Path"))
    layout.addWidget(inspector.path)
    layout.addWidget(browse_button)
    layout.addWidget(inspector.status)
    return inspector
