from typing import List
import dill

from Model.Program.Parameter import Parameter


class Program:
    def __init__(self):
        self.parameters: List[Parameter] = []
        self.name = "New Program"

        self.libraryPath = None

        self.description = ""

        self.script = """"""

    def GetFormattedScript(self):
        header = "def Execute():\n    "

        if self.script:
            return header + self.script.replace("\n", "\n    ").replace("\t", "    ")
        else:
            return header + "pass"

    def __setstate__(self, state):
        self.__dict__ = state
        if 'libraryPath' not in self.__dict__:
            self.libraryPath = None
        if 'description' not in self.__dict__:
            self.description = ""

    def Export(self, path):
        file = open(path, "wb+")
        dill.dump(self, file)
        file.close()

    @staticmethod
    def LoadFromFile(path):
        file = open(path, "rb")
        program = dill.load(file)
        file.close()

        return program
