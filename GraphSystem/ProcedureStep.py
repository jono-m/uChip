from GraphSystem.GraphBlock import GraphBlock


class ProcedureStep:
    def __init__(self, graphBlock: GraphBlock):
        super().__init__()

        self._graphBlock = graphBlock
        self._isRunning = False
        self._hasRun = False
        self._progress = 0.0

    def IsRunning(self):
        return self._isRunning

    def HasRun(self):
        return self._hasRun

    def GetGraphBlock(self):
        return self._graphBlock

    def SetProgress(self, progress):
        self._progress = max(0.0, min(1.0, progress))

    def GetProgress(self):
        if self._isRunning:
            return self._progress
        else:
            if self._hasRun:
                return 1.0
            else:
                return 0.0

    def OnProcedureStarted(self):
        self._hasRun = False

    def OnStepStarted(self):
        self._isRunning = True

    def OnStepTick(self):
        pass

    def OnStepCompleted(self):
        self._isRunning = False
        self._hasRun = True

    def OnProcedureCompleted(self):
        self._isRunning = False
