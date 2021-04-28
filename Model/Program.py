from enum import Enum, auto
from Parameter import Parameter
from ParameterValue import ParameterValue
import typing


class Program:
    def __init__(self):
        self.parameters: typing.List[Parameter] = []

    def Execute(self, parameterValues: typing.Dict['Parameter', 'ParameterValue']):
        pass


class ScriptedProgram(Program):
    def __init__(self):
        super().__init__()

        # Signature: Parameters(
        self.parametersScript