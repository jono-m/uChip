import typing
from ParameterValue import ParameterValue

class Parameter:
    def __init__(self):
        self.name = ""
        self.valueType: typing.Optional[typing.Type[ParameterValue]] = None

