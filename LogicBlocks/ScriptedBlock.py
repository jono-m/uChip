from LogicBlocks.LogicBlock import *


class ScriptedBlock(LogicBlock):
    def __init__(self, scriptFilename):
        super().__init__()
        self.goodBuiltins = ['abs', 'ascii', 'bin', 'chr', 'hex', 'iter', 'len', 'max', 'min', 'next', 'oct', 'ord',
                             'pow',
                             'round', 'sorted', 'sum', 'None', 'Ellipsis', 'False', 'True', 'bool', 'bytes', 'complex',
                             'dict', 'float', 'int', 'list', 'map', 'range', 'reversed', 'set', 'slice', 'str', 'tuple',
                             'zip']

        self.scriptFilename = scriptFilename
        self.code = ""
        self.codeLocals = {}
        self.codeGlobals = {}

        self.Reload()

    def Reload(self):
        f = open(self.scriptFilename)
        self.code = f.read()
        f.close()
        self.codeGlobals = {'__builtins__': {k: __builtins__[k] for k in self.goodBuiltins}}
        self.codeLocals = {}
        exec(self.code, self.codeGlobals, self.codeLocals)

        for inputPort in self.GetInputs():
            self.RemoveInput(inputPort)
        for outputPort in self.GetOutputs():
            self.RemoveOutput(outputPort)

        inputs = self.codeLocals['Inputs']()
        outputs = self.codeLocals['Outputs']()
        for portName in inputs:
            self.AddInput(portName, inputs[portName])
        for portName in outputs:
            self.AddOutput(portName, outputs[portName])

    def GetName(self=None):
        if self is None:
            return "Scripted Block"
        else:
            return self.codeLocals['blockName']

    def UpdateOutputs(self):
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
