import typing
from enum import Enum, auto
from pathlib import Path
from ProjectSystem.Project import Project
from ProjectSystem.ChipProject import ChipProject
from ProjectSystem.BlockGraphProject import BlockGraphProject
from ProjectSystem.BlockScriptProject import BlockScriptProject


class ProjectType(Enum):
    CHIP_PROJECT = auto()
    BLOCK_GRAPH = auto()
    BLOCK_SCRIPT = auto()

    def typeName(self):
        return {ProjectType.CHIP_PROJECT: "Chip Project",
                ProjectType.BLOCK_GRAPH: "Block Graph Project",
                ProjectType.BLOCK_SCRIPT: "Block Script Project"}[self]

    def description(self):
        return {ProjectType.CHIP_PROJECT: "A project to program and control a microfluidic chip.",
                ProjectType.BLOCK_GRAPH: "A custom logic block based on a block graph.",
                ProjectType.BLOCK_SCRIPT: "A custom logic block based on a script."}[self]

    def fileExtension(self):
        return {ProjectType.CHIP_PROJECT: ".ucc",
                ProjectType.BLOCK_GRAPH: ".ucg",
                ProjectType.BLOCK_SCRIPT: ".ucs"}[self]

    def modelClass(self) -> typing.Type[Project]:
        return {ProjectType.CHIP_PROJECT: ChipProject,
                ProjectType.BLOCK_GRAPH: BlockGraphProject,
                ProjectType.BLOCK_SCRIPT: BlockScriptProject}[self]

    def fileFilter(self):
        return self.typeName() + "(*" + self.fileExtension() + ")"

    @staticmethod
    def TypeFromPath(path: Path) -> typing.Optional['ProjectType']:
        matches = [projectType for projectType in ProjectType if projectType.fileExtension() == path.suffix]
        if matches:
            return matches[0]
        else:
            return None

    @staticmethod
    def allFilter():
        return "uChip Files (" + " ".join(["*" + newType.fileExtension() for newType in ProjectType]) + ")"
