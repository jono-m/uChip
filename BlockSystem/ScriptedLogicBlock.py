from BaseLogicBlock import BaseLogicBlock


class ScriptedLogicBlock(BaseLogicBlock):
    def GetName(self):
        if self is None:
            return "Scripted Block"
        else:
            return self._codeLocals['blockName']

    def __init__(self):
        super().__init__()
        self._goodBuiltins = ['abs', 'ascii', 'bin', 'chr', 'hex', 'iter', 'len', 'max', 'min', 'next', 'oct', 'ord',
                              'pow',
                              'round', 'sorted', 'sum', 'None', 'Ellipsis', 'False', 'True', 'bool', 'bytes', 'complex',
                              'dict', 'float', 'int', 'list', 'map', 'range', 'reversed', 'set', 'slice', 'str',
                              'tuple',
                              'zip']

        self._codeLocals = {}
        self._codeGlobals = {}

    def ParseCode(self, code: str):
        self._codeGlobals = {'__builtins__': {k: __builtins__[k] for k in self._goodBuiltins}}
        self._codeLocals = {}
        exec(code, self._codeGlobals, self._codeLocals)

    def SyncInputPorts(self):
        inputPortsDict = list(eval("Inputs()", self._codeLocals, self._codeGlobals).items())

        unMatchedInputs = self.GetInputPorts().copy()
        for inputPort in inputPortsDict.copy():
            inputName, (dataType, defaultValue) = inputPort
            matchingInputs = [unMatchedInputs[idx] for idx, unMatchedInput in enumerate(unMatchedInputs) if
                              unMatchedInput.name == inputName]
            if matchingInputs:
                # Found a name match, remove it
                if matchingInputs[0].dataType != dataType:
                    matchingInputs[0].dataType = dataType
                    matchingInputs[0].SetDefaultValue(defaultValue)
                unMatchedInputs.remove(matchingInputs[0])
                inputPortsDict.remove(inputPort)
                break

        # Match the rest in order
        for inputPort in inputPortsDict.copy():
            inputName, (dataType, defaultValue) = inputPort
            if unMatchedInputs:
                toMatch = unMatchedInputs.pop(0)
                toMatch.name = inputName
                if toMatch.dataType != dataType:
                    toMatch.dataType = dataType
                    toMatch.SetDefaultValue(defaultValue)
                inputPortsDict.remove(inputPort)
            else:
                # Ran out of ports.
                break

        # Create any new ones needed
        for inputPort in inputPortsDict.copy():
            inputName, (dataType, defaultValue) = inputPort
            self.CreateInputPort(inputName, dataType, defaultValue)

        # Remove any ones that weren't matched
        for inputPort in unMatchedInputs:
            self.RemovePort(inputPort)

    def SyncOutputPorts(self):
        outputPortsDict = list(eval("Outputs()", self._codeLocals, self._codeGlobals).items())

        unMatchedOutputs = self.GetOutputPorts().copy()
        for outputPort in outputPortsDict.copy():
            outputName, dataType = outputPort
            matchingOutputs = [unMatchedOutputs[idx] for idx, unMatchedOutput in enumerate(unMatchedOutputs) if
                               unMatchedOutput.name == outputName]
            if matchingOutputs:
                # Found a name match, remove it
                matchingOutputs[0].dataType = dataType
                unMatchedOutputs.remove(matchingOutputs[0])
                outputPortsDict.remove(outputPort)
                break

        # Match the rest in order
        for outputPort in outputPortsDict.copy():
            outputName, dataType = outputPort
            if unMatchedOutputs:
                toMatch = unMatchedOutputs.pop(0)
                toMatch.name = outputName
                toMatch.dataType = dataType
                outputPortsDict.remove(outputPort)
            else:
                # Ran out of ports.
                break

        # Create any new ones needed
        for outputPort in outputPortsDict.copy():
            outputName, dataType = outputPort
            self.CreateOutputPort(outputName, dataType)

        # Remove any ones that weren't matched
        for outputPort in unMatchedOutputs:
            self.RemovePort(outputPort)

    def SyncParameters(self):
        parametersDict = list(eval("Parameters()", self._codeLocals, self._codeGlobals).items())

        unMatchedParameters = self.GetParameters().copy()
        for parameter in parametersDict.copy():
            parameterName, (dataType, defaultValue) = parameter
            matchingParameters = [unMatchedParameters[idx] for idx, unMatchedParameter in enumerate(unMatchedParameters)
                                  if unMatchedParameter.name == parameterName]
            if matchingParameters:
                # Found a name match, remove it
                if matchingParameters[0].dataType != dataType:
                    matchingParameters[0].dataType = dataType
                    matchingParameters[0].SetValue(defaultValue)
                unMatchedParameters.remove(matchingParameters[0])
                parametersDict.remove(parameter)
                break

        # Match the rest in order
        for parameter in parametersDict.copy():
            parameterName, (dataType, defaultValue) = parameter
            if unMatchedParameters:
                toMatch = unMatchedParameters.pop(0)
                toMatch.name = parameterName
                if toMatch.dataType != dataType:
                    toMatch.dataType = dataType
                    toMatch.SetValue(defaultValue)
                parametersDict.remove(parameter)
            else:
                # Ran out of ports.
                break

        # Create any new ones needed
        for parameter in parametersDict.copy():
            parameterName, (dataType, defaultValue) = parameter
            self.CreateParameter(parameterName, dataType, defaultValue)

        # Remove any ones that weren't matched
        for parameter in unMatchedParameters:
            self.RemoveParameter(parameter)

    def Update(self):
        super().Update()

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

        # Set up any new ports as needed
        self.SyncParameters()
        self.SyncInputPorts()
        self.SyncOutputPorts()

        # Compute outputs
        outputValues = {}
        self._codeLocals['outputs'] = outputValues
        exec("Compute(inputs, outputs)", self._codeGlobals, self._codeLocals)

        # Flush the output values to ports
        for outputPort in self.GetOutputPorts():
            if outputPort.name in outputValues:
                outputPort.SetValue(outputValues[outputPort.name])
