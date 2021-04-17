from ProjectSystem.Project import Project
from GraphSystem.BaseConnectableBlock import GraphBlock
from GraphSystem.DataPorts import InputPort, OutputPort, DataPort
from GraphSystem.Data import Data, MatchData
import typing


# A Block that internally executes a block system project.
class ProjectBlock(GraphBlock):
    def GetName(self):
        if not self.IsValid():
            return "Invalid Project Block"
        return self._project.GetProjectName()

    def __init__(self):
        super().__init__()
        self._project: typing.Optional[Project] = None
        self._inputPairs: typing.List[typing.Tuple[InputPort, Data]] = []
        self._settingPairs: typing.List[typing.Tuple[Data, Data]] = []
        self._outputPairs: typing.List[typing.Tuple[OutputPort, Data]] = []

    def IsValid(self):
        return self._project is not None and all([block.IsValid() for block in self._project.GetProjectBlocks()])

    def LoadProject(self, project: Project):
        self._project = project
        self.Sync()

    def ContainsProject(self, project: Project):
        if project == self._project:
            return True
        else:
            return any(block.ContainsProject(project) for block in self._project.GetProjectBlocks() if
                       isinstance(block, ProjectBlock))

    # Tries to sync the ports and settings by name.
    def Sync(self):
        self._inputPairs.clear()
        self._settingPairs.clear()
        self._outputPairs.clear()

        (matchedInputs, newSettings, oldInputs) = MatchData(self._project.GetInputs().copy(),
                                                            [port.GetDataReference() for port in
                                                             self.GetPorts(InputPort)])
        (matchedSettings, newSettings, oldSettings) = MatchData(self._project.GetSettings().copy(),
                                                                self.GetSettings().copy())
        (matchedOutputs, newOutputs, oldOutputs) = MatchData(self._project.GetOutputs().copy(),
                                                             [port.GetDataReference() for port in
                                                              self.GetPorts(OutputPort)])

        [self.RemovePort(port) for port in self.GetPorts(DataPort) if port.GetDataReference() in (oldInputs + oldOutputs)]
        [self.RemoveSetting(setting) for setting in self.GetSettings().copy() if setting in oldSettings]

        for (projectInput, portData) in matchedInputs:
            port = [port for port in self.GetPorts(DataPort) if port.GetDataReference() == portData][0]
            self._inputPairs.append((port, projectInput))

        for (projectOutput, portData) in matchedOutputs:
            port = [port for port in self.GetPorts(OutputPort) if port.GetDataReference() == portData][0]
            self._outputPairs.append((port, projectOutput))

        for (projectSetting, blockSetting) in matchedSettings:
            self._settingPairs.append((blockSetting, projectSetting))

        for newSetting in newSettings:
            self._inputPairs.append((self.AddPort(InputPort(newSetting.Copy())), newSetting))

        for newOutput in newOutputs:
            self._outputPairs.append((self.AddPort(OutputPort(newOutput.Copy())), newOutput))

        for newSetting in newSettings:
            self._settingPairs.append((self.AddSetting(newSetting.Copy()), newSetting))

    def Update(self):
        super().Update()

        if not self.IsValid():
            return

        for (inputPort, projectInput) in self._inputPairs:
            projectInput.SetValue(inputPort.GetValue())
        for (blockSetting, projectSetting) in self._settingPairs:
            projectSetting.SetValue(blockSetting.GetValue())
        self._project.UpdateBlocks()
        for (outputPort, projectOutput) in self._outputPairs:
            outputPort.SetValue(projectOutput.GetValue())
