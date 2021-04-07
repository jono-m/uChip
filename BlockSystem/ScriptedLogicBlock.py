from BlockSystem.BaseLogicBlock import BaseLogicBlock, LogicPortTypeSpec
from BlockSystem.BaseConnectableBlock import ParameterTypeSpec
import typing

ParametersSpec = typing.Dict[str, typing.Tuple[ParameterTypeSpec, typing.Any]]
InputPortsSpec = typing.Dict[str, typing.Tuple[LogicPortTypeSpec, typing.Any]]
OutputPortsSpec = typing.Dict[str, typing.Tuple[LogicPortTypeSpec, typing.Any]]

InputDataSpec = typing.Dict[str, typing.Any]
ParameterDataSpec = typing.Dict[str, typing.Any]
OutputDataSpec = typing.Dict[str, typing.Any]

GetNameSpec = typing.Callable[[ParameterDataSpec], str]
GetParametersSpec = typing.Callable[[], ParametersSpec]
GetInputPortsSpec = typing.Callable[[ParametersSpec], InputPortsSpec]
GetOutputPortsSpec = typing.Callable[[ParametersSpec], OutputPortsSpec]

ComputeOutputsSpec = typing.Callable[[InputDataSpec, ParameterDataSpec], OutputDataSpec]


class ScriptedLogicBlock(BaseLogicBlock):
    def GetName(self):
        if self._nameFunc is None:
            return "Unnamed Scripted Logic Block"

    def __init__(self):
        super().__init__()
        self._nameFunc: typing.Optional[GetNameSpec] = None

        self._computeOutputs: typing.Optional[ComputeOutputsSpec] = None
        self._getParameters: typing.Optional[GetParametersSpec] = None
        self._getInputPorts: typing.Optional[GetInputPortsSpec] = None
        self._getOutputPorts: typing.Optional[GetOutputPortsSpec] = None

        self.com

    def Compile(self):

    def Update(self):
        super().Update()

        if not self.IsValid():
            return

        # Copy over input values from ports
        inputValues = {}
        for inputPort in self.GetInputPorts():
            inputValues[inputPort.name] = inputPort.GetValue()
        self._codeLocals['inputs'] = inputValues

        # Copy over parameter values from block parameters
        parameterValues = {}
        for parameter in self.GetParameters():
            parameterValues[parameter.name] = parameter.GetValue()
        self._codeLocals['parameters'] = parameterValues
        try:
            # Set up any new ports as needed
            self.SyncParameters()
            self.SyncInputPorts()
            self.SyncOutputPorts()

            # Compute outputs
            outputValues = {}
            self._codeLocals['outputs'] = outputValues
            exec("Compute(inputs, outputs)", self._codeGlobals, self._codeLocals)
        except Exception as e:
            self.SetInvalid("Script execution error:\n" + str(e))
            return

        # Flush the output values to ports
        for outputPort in self.GetOutputPorts():
            if outputPort.name in outputValues:
                outputPort.SetValue(outputValues[outputPort.name])
