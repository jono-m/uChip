from ProjectEntity import ProjectEntity
from pathlib import Path


class Image(ProjectEntity):
    def __init__(self, path: Path):
        super().__init__()
        self.editableProperties['imagePath'] = path
        self.editableProperties['scale'] = 1
        self.editableProperties['opacity'] = 1
