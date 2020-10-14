from ChipController.ChipController import *
from UI.LogicBlock.LogicBlockEditor import *
from UI.Procedure.StepBlockItem import *
from UI.Procedure.StepConnection import *


class ProcedureEditor(LogicBlockEditor):
    def __init__(self):
        super().__init__()

        self.procedure: typing.Optional[Procedure] = None

        self.worldBrowser.tempConnectionLine.GetPath = lambda a, b: self.GetPath(a, b)

        self.worldBrowser.gridSpacing = QSize(0, 100)

    def Clear(self):
        self.procedure = None
        super().Clear()

    def CreateBlockItem(self, newBlock: LogicBlock):
        if isinstance(newBlock, Step):
            return StepBlockItem(self.worldBrowser.scene(), newBlock)
        return super().CreateBlockItem(newBlock)

    def LoadProcedure(self, procedure: Procedure):
        super().LoadBlock(procedure)

        stepItems = [x for x in self.worldBrowser.scene().items() if isinstance(x, StepBlockItem)]

        # Go over each loaded block
        for stepItem in stepItems:
            # Connect each completed in the block
            for completedPort in stepItem.step.GetCompletedPorts():
                # To each input
                for beginPort in completedPort.connectedBegin:
                    self.CreateConnectionItem((completedPort, beginPort))
    
    def CreateConnectionItem(self, ports: typing.Tuple[Port, Port]):
        if not (isinstance(ports[0], CompletedPort) and isinstance(ports[1], BeginPort)):
            super().CreateConnectionItem(ports)
            return

        stepItems = [stepItem for stepItem in self.worldBrowser.scene().items() if
                     isinstance(stepItem, StepBlockItem)]

        foundBeginWidget: typing.Optional[BeginPortWidget] = None

        foundCompletedWidget: typing.Optional[CompletedPortWidget] = None

        for stepItem in stepItems:
            if foundBeginWidget is None and stepItem.step == ports[1].block:
                beginWidgets = [x for x in stepItem.beginPortsWidget.children() if isinstance(x, BeginPortWidget)]
                for beginWidget in beginWidgets:
                    if beginWidget.beginPort == ports[1]:
                        foundBeginWidget = beginWidget
                        break
            if foundCompletedWidget is None and stepItem.step == ports[0].block:
                completedWidgets = [x for x in stepItem.completedPortsWidget.children() if
                                    isinstance(x, CompletedPortWidget)]
                for completedWidget in completedWidgets:
                    if completedWidget.completedPort == ports[0]:
                        foundCompletedWidget = completedWidget
                        break

        if foundBeginWidget is not None and foundCompletedWidget is not None:
            return StepConnection(self.worldBrowser.scene(), foundBeginWidget.portHole, foundCompletedWidget.portHole)