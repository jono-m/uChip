from LogicBlocks.LogicBlock import *
import os


class ScriptedBlock(LogicBlock):
    def __init__(self, scriptFilename):
        super().__init__()
        self._goodBuiltins = ['abs', 'ascii', 'bin', 'chr', 'hex', 'iter', 'len', 'max', 'min', 'next', 'oct', 'ord',
                             'pow',
                             'round', 'sorted', 'sum', 'None', 'Ellipsis', 'False', 'True', 'bool', 'bytes', 'complex',
                             'dict', 'float', 'int', 'list', 'map', 'range', 'reversed', 'set', 'slice', 'str', 'tuple',
                             'zip']

        self._scriptFilename = scriptFilename
        self._lastModifiedTime = None
        self._code = ""
        self._codeLocals = {}
        self._codeGlobals = {}

        self.Reload()

    def Reload(self):
        if not os.path.exists(self._scriptFilename):
            self.Destroy()
            return
        f = open(self._scriptFilename)
        self._lastModifiedTime = os.path.getmtime(self._scriptFilename)
        self._code = f.read()
        f.close()
        self._codeGlobals = {'__builtins__': {k: __builtins__[k] for k in self._goodBuiltins}}
        self._codeLocals = {}
        exec(self._code, self._codeGlobals, self._codeLocals)

        newInputs = self._codeLocals['Inputs']()
        newOutputs = self._codeLocals['Outputs']()

        oldInputs = self.GetInputs()
        oldOutputs = self.GetOutputs()

        # Match reloaded ports to existing ports. Create new ones if no match was found
        for newInputPortName in newInputs:
            found = False
            for oldInput in oldInputs:
                if oldInput.name == newInputPortName and oldInput.dataType == newInputs[newInputPortName]:
                    oldInputs.remove(oldInput)
                    found = True
                    break
            if not found:
                self.AddInput(newInputPortName, newInputs[newInputPortName])

        for newOutputPortName in newOutputs:
            found = False
            for oldOutput in oldOutputs:
                if oldOutput.name == newOutputPortName and oldOutput.dataType == newOutputs[newOutputPortName]:
                    oldOutputs.remove(oldOutput)
                    found = True
                    break
            if not found:
                self.AddOutput(newOutputPortName, newOutputs[newOutputPortName])

        # Remove any existing ports that were not matched to reloaded ports
        for oldOutput in oldOutputs:
            self.RemoveOutput(oldOutput)

        for oldInput in oldInputs:
            self.RemoveInput(oldInput)

    def GetName(self=None):
        if self is None:
            return "Scripted Block"
        else:
            return self._codeLocals['blockName']

    def Duplicate(self) -> 'LogicBlock':
        newB = ScriptedBlock(self._scriptFilename)
        for i in range(len(self._inputs)):
            newB._inputs[i].SetDefaultData(self._inputs[i].GetDefaultData())
        newB.SetPosition(self.GetPosition())
        self.OnDuplicated.Invoke(newB)
        return newB

    def UpdateOutputs(self):

        inputs = {}
        for inputPort in self.GetInputs():
            inputs[inputPort.name] = inputPort.GetData()
        outputs = {}
        self._codeLocals['inputs'] = inputs
        self._codeLocals['outputs'] = outputs
        eval("Compute(inputs, outputs)", self._codeGlobals, self._codeLocals)
        for outputPort in self.GetOutputs():
            if outputPort.name in outputs:
                outputPort.SetData(outputs[outputPort.name])
        super().UpdateOutputs()
