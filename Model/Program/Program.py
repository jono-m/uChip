from typing import List

from Model.Program.Parameter import Parameter


class Program:
    def __init__(self):
        self.parameters: List[Parameter] = []
        self.name = "New Program"

        self.script = """"""

    def FormatScript(self):
        header = "def Execute():\n    "

        if self.script:
            return header + self.script.replace("\n", "\n    ").replace("\t", "    ")
        else:
            return header + "pass"
