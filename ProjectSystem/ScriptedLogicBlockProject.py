from ProjectTypes.Project import Project
from ProjectTypes.ProjectEntity import ProjectEntity
from GraphSystem.Data import Data, MatchData
import typing


class ScriptEntity(ProjectEntity):
    def __init__(self, code: str):
        super().__init__()
        self.editableProperties['code'] = code

    def GetCode(self):
        return self.editableProperties['code']


class ScriptedLogicBlockProject(Project):
    def __init__(self):
        super().__init__()
        self._executedCodeEnvironment = {}

        self.getNameScript = self.AddEntity(ScriptEntity("return \"Scripted Logic Block\""))
        self.getSettingsScript = self.AddEntity(ScriptEntity("return {}"))
        self.getIOScript = self.AddEntity(ScriptEntity("return {}"))
        self.computeOutputsScript = self.AddEntity(ScriptEntity("return {}"))

        self._outputs: typing.List[Data] = []
        self.Recompile()

    def GetOutputs(self):
        return self._outputs

    def GetProjectName(self):
        return eval("GetName(settings)", self._executedCodeEnvironment, {'settings': self.GetPackedCurrentSettings()})

    @staticmethod
    def GetNameScriptHeader():
        return "# settings:  A dictionary mapping setting names to their current values.\n" \
               "# RETURN:    A string that is the current name of the block." \
               "def GetName(settings: Dict[str, Any]) -> str:"

    @staticmethod
    def GetIOScriptHeader():
        return "# settings:  A dictionary mapping setting names to their current values.\n" \
               "# RETURN:    A tuple. \n" \
               "#            The first entry is a dictionary that maps from input names to their data type.\n" \
               "#            The second entry is a dictionary that maps from output names to their data type.\n" \
               "#            NOTE: A data type of None means that data will not be typecast.\n" \
               "def GetIO(settings: Dict[str, Any]) -> " \
               "    Tuple[Dict[str, Union[Type, List, None]]], Dict[str, Union[Type, List, None]]]:"

    @staticmethod
    def GetSettingsScriptHeader():
        return "# RETURN: A dictionary that maps from setting names to their data type.\n" \
               "def GetSettings() -> Dict[str, Union[Type, List]]):"

    @staticmethod
    def ComputeOutputsScriptHeader():
        return "# settings: A dictionary mapping setting names to their current values.\n" \
               "# inputs: A dictionary mapping input port names to their current values.\n" \
               "# RETURN: A dictionary that maps from output port names to their new values.\n" \
               "def ComputeOutputs(settings: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]]):"

    @staticmethod
    def IndentAll(code: str):
        return ("\t" + code).replace("\n", "\n\t").replace("\t", "    ")

    def Recompile(self):
        getNameScript = self.GetNameScriptHeader() + "\n" + self.IndentAll(
            self.getNameScript.GetCode()) + "\n"
        getSettingsScript = self.GetSettingsScriptHeader() + "\n" + self.IndentAll(
            self.getSettingsScript.GetCode()) + "\n"
        getIOScript = self.GetIOScriptHeader() + "\n" + self.IndentAll(
            self.getIOScript.GetCode()) + "\n"
        computeOutputsScript = self.ComputeOutputsScriptHeader() + "\n" + self.IndentAll(
            self.computeOutputsScript.GetCode()) + "\n"

        fullCode = getNameScript + getIOScript + getSettingsScript + computeOutputsScript

        self._executedCodeEnvironment = {}
        exec(fullCode, self._executedCodeEnvironment)

        settingsDict = eval("GetSettings()", self._executedCodeEnvironment)
        settings = [Data(name, settingsDict[name]) for name in settingsDict]

        (_, newSettings, oldSettings) = MatchData(settings, self.GetSettings())
        for newSetting in newSettings:
            self.AddSetting(newSetting)
        for oldSetting in oldSettings:
            self.RemoveSetting(oldSetting)

        self.UpdatePorts()

    def UpdatePorts(self):
        (inputsDict, outputsDict) = eval("GetIO(settings)", self._executedCodeEnvironment,
                                         {'settings': self.GetPackedCurrentSettings()})
        inputs = [Data(name, inputsDict[name]) for name in inputsDict]
        outputs = [Data(name, outputsDict[name]) for name in outputsDict]
        (_, newInputs, oldInputs) = MatchData(inputs, self.GetInputs())
        for newInput in newInputs:
            self.AddInput(newInput)
        for oldInput in oldInputs:
            self.RemoveInput(oldInput)
        (_, newOutputs, oldOutputs) = MatchData(outputs, self.GetOutputs())
        for newOutput in newOutputs:
            self._outputs.append(newOutput)
        for oldOutput in oldOutputs:
            self._outputs.remove(oldOutput)

    def UpdateBlocks(self):
        self.UpdatePorts()
        outputs = eval('ComputeOutputs(settings, inputs)', self._executedCodeEnvironment,
                       {'settings': self.GetPackedCurrentSettings(),
                        'inputs': self.GetPackedCurrentInputs()})
        [output.SetValue(outputs[output.GetName()]) for output in self.GetOutputs()]

    def GetPackedCurrentSettings(self):
        return {setting.name: setting.GetValue() for setting in self.GetSettings()}

    def GetPackedCurrentInputs(self):
        return {inputData.name: inputData.GetValue() for inputData in self.GetInputs()}
