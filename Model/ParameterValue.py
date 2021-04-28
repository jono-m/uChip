import typing


class ParameterValue:
    def __init__(self, initialValue):
        self.value = initialValue


class NumberValue(ParameterValue):
    def __init__(self):
        super().__init__(0)

        self.minimum = None
        self.step = None
        self.maximum = None

        self.integersOnly = False


class BooleanValue(ParameterValue):
    def __init__(self):
        super().__init__(False)


class ListValue(ParameterValue):
    def __init__(self):
        super().__init__(0)
        self.options: typing.List[str] = []
