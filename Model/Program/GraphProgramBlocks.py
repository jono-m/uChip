from GraphProgram import GraphBlock, InputPort, OutputPort, BeginPort, CompletedPort
from Program import Parameter


class ParameterBlock(GraphBlock):
    def GetName(self):
        return "Parameter: " + self.parameter.name

    def __init__(self, parameter: Parameter):
        super().__init__()

        self.parameter = parameter
        self.parameterOutputPort = OutputPort("Value", self, parameter.dataType, )
        self.outputPorts +=

    def ComputeOutputs(self, inputData: typing.Dict['InputPort', typing.Any], instance: ProgramInstance) -> typing.Dict[
        'OutputPort', typing.Any]:
