from ProjectTab import ProjectTab
from ProjectSystem.ChipProject import ChipProject, ChipProgram


class ChipProgramTab(ProjectTab):
    def __init__(self, chipProject: ChipProject, program: ChipProgram):
        super().__init__(chipProject)

        self._program = program

    def GetTitle(self):
        return self._program.GetName() + " (PROGRAM)"

    def RequestClose(self):
        return True

    def GetPath(self):
        return None
