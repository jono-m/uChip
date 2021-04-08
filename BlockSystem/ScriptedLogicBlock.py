from BlockSystem.BaseLogicBlock import BaseLogicBlock
from BlockSystem.Util import SyncPorts, SyncParameters
from typing import Dict, Any


class ScriptedLogicBlock(BaseLogicBlock):
    def GetName(self):
        localData = {'parameterValues': self.GetPackedParameterValues()}
        return eval("GetName(parameterValues)", self._executedCodeEnvironment, localData)

    def __init__(self):
        super().__init__()
        self._executedCodeEnvironment = {}

    @staticmethod
    def GetNameScriptHeader():
        return "# parameterValues: A dictionary mapping parameter names to their current values.\n" \
               "# return: A string that is the current name of the block." \
               "def GetName(parameterValues: Dict[str, Any]) -> str:"

    @staticmethod
    def GetPortsScriptHeader():
        return "# parameterValues: A dictionary mapping parameter names to their current values.\n" \
               "# return: A tuple. \n" \
               "#         The first entry is a dictionary that maps from input port names to a tuple of their data type and initial value.\n" \
               "#         The second entry is a dictionary that maps from output port names to their data type.\n" \
               "def GetPorts(parameterValues: Dict[str, Any]) -> Tuple[Dict[str, Tuple[Union[Type, List, None], Any]], Dict[str, Union[Type, List, None]]]:"

    @staticmethod
    def GetParameterScriptHeader():
        return "# return: A dictionary that maps from parameter names to a tuple of their data type and initial value.\n" \
               "def GetParameters() -> Dict[str, Tuple[Union[Type, List], Any]]):"

    @staticmethod
    def GetComputeOutputsScriptHeader():
        return "# parameterValues: A dictionary mapping parameter names to their current values.\n" \
               "# inputValues: A dictionary mapping input port names to their current values.\n" \
               "# return: A dictionary that maps from output port names to their new values.\n" \
               "def ComputeOutputs(parameterValues: Dict[str, Any], inputValues: Dict[str, Any]) -> Dict[str, Any]]):"

    @staticmethod
    def IndentAll(code: str):
        return ("\t" + code).replace("\n", "\n\t").replace("\t", "    ")

    def Execute(self, getNameScript, getPortsScript, getParametersScript, computeOutputsScript):
        getNameScript = ScriptedLogicBlock.GetNameScriptHeader() + "\n" + ScriptedLogicBlock.IndentAll(
            getNameScript) + "\n"
        getPortsScript = ScriptedLogicBlock.GetPortsScriptHeader() + "\n" + ScriptedLogicBlock.IndentAll(
            getPortsScript) + "\n"
        getParametersScript = ScriptedLogicBlock.GetParameterScriptHeader() + "\n" + ScriptedLogicBlock.IndentAll(
            getParametersScript) + "\n"
        computeOutputsScript = ScriptedLogicBlock.GetComputeOutputsScriptHeader() + "\n" + ScriptedLogicBlock.IndentAll(
            computeOutputsScript) + "\n"
        fullCode = getNameScript + getPortsScript + getParametersScript + computeOutputsScript

        self._executedCodeEnvironment = {}
        exec(fullCode, self._executedCodeEnvironment)

        parameters = eval("GetParameters()", self._executedCodeEnvironment)
        SyncParameters(self, parameters)
        localData = {'parameterValues': self.GetPackedParameterValues()}
        (inputPorts, outputPorts) = eval("GetPorts(parameterValues)", self._executedCodeEnvironment, localData)
        SyncPorts(self, inputPorts, outputPorts)

    def ComputeOutputs(self):
        localData = {'parameterValues': self.GetPackedParameterValues(),
                     'inputValues': self.GetPackedInputValues()}
        outputValues = eval("ComputeOutputs(parameterValues, inputValues)", self._executedCodeEnvironment, localData)
        self.UnpackOutputs(outputValues)

    def GetPackedParameterValues(self):
        values = {}
        for parameter in self.GetParameters():
            values[parameter.name] = parameter.GetValue()
        return values

    def GetPackedInputValues(self):
        values = {}
        for inputPort in self.GetInputPorts():
            values[inputPort.name] = inputPort.GetValue()
        return values

    def UnpackOutputs(self, outputsDict: Dict[str, Any]):
        for outputPortName in outputsDict:
            matchingOutput = [port for port in self.GetOutputPorts() if port.name == outputPortName]
            if matchingOutput:
                matchingOutput[0].SetValue(outputsDict[outputPortName])

    def Update(self):
        super().Update()

        if not self.IsValid():
            return

        try:
            self.ComputeOutputs()
        except Exception as e:
            self.SetInvalid("Script execution error:\n" + str(e))
