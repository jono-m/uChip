from LogicBlocks.LogicBlock import *
import os


class ScriptedBlock(LogicBlock):
    def __init__(self, scriptFilename):
        super().__init__()
        self.goodBuiltins = ['abs', 'ascii', 'bin', 'chr', 'hex', 'iter', 'len', 'max', 'min', 'next', 'oct', 'ord',
                             'pow',
                             'round', 'sorted', 'sum', 'None', 'Ellipsis', 'False', 'True', 'bool', 'bytes', 'complex',
                             'dict', 'float', 'int', 'list', 'map', 'range', 'reversed', 'set', 'slice', 'str', 'tuple',
                             'zip']

        self.scriptFilename = scriptFilename
        self.lastModifiedTime = None
        self.code = ""
        self.codeLocals = {}
        self.codeGlobals = {}

        self.Reload()

    def Reload(self):
        if not os.path.exists(self.scriptFilename):
            print("Destroyed " + self.scriptFilename)
            self.Destroy()
            return
        print("Reloaded " + self.scriptFilename)
        f = open(self.scriptFilename)
        self.lastModifiedTime = os.path.getmtime(self.scriptFilename)
        self.code = f.read()
        f.close()
        self.codeGlobals = {'__builtins__': {k: __builtins__[k] for k in self.goodBuiltins}}
        self.codeLocals = {}
        exec(self.code, self.codeGlobals, self.codeLocals)

        newInputs = self.codeLocals['Inputs']()
        newOutputs = self.codeLocals['Outputs']()

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
            return self.codeLocals['blockName']

    def UpdateOutputs(self):
        currentModifiedTime = os.path.getmtime(self.scriptFilename)
        if currentModifiedTime != self.lastModifiedTime:
            self.Reload()

        inputs = {}
        for inputPort in self.GetInputs():
            inputs[inputPort.name] = inputPort.GetData()
        outputs = {}
        self.codeLocals['inputs'] = inputs
        self.codeLocals['outputs'] = outputs
        eval("Compute(inputs, outputs)", self.codeGlobals, self.codeLocals)
        for outputPort in self.GetOutputs():
            if outputPort.name in outputs:
                outputPort.SetData(outputs[outputPort.name])
        super().UpdateOutputs()
