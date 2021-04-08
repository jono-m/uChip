import typing
from typing import List, Tuple, Type, Union, Dict, Any
from BaseLogicBlock import BaseLogicBlock


def DatatypeToName(dataType: typing.Type) -> str:
    if dataType == list:
        return "Option"
    if dataType == int or dataType == float:
        return "Number"
    if dataType == str:
        return "Text"
    if dataType == bool:
        return "True/False"
    else:
        return str(dataType).split('\'')[1].capitalize()


NamesTypesPair = Tuple[str, Union[Type, List, None]]


def MatchNamesAndTypes(nextNameTypesList: List[NamesTypesPair], currentNameTypesList: List[NamesTypesPair]) -> \
        Tuple[List[Tuple[str, str]], List[str], List[str]]:
    # Names that match exactly
    sameNameTypes = [nextNameType for nextNameType in nextNameTypesList if
                     nextNameType[0] in [currentNameType[0] for currentNameType in currentNameTypesList]]

    # New names that don't match
    newNameTypes = [nextNameType for nextNameType in nextNameTypesList if
                    nextNameType[0] not in [currentNameType[0] for currentNameType in currentNameTypesList]]

    # Old names that don't match
    oldNameTypes = [currentNameType for currentNameType in currentNameTypesList if
                    currentNameType[0] not in [nextNameType[0] for nextNameType in nextNameTypesList]]

    # Add the exact matches
    matchedNames = [(sameNameType[0], sameNameType[0]) for sameNameType in sameNameTypes]

    # Try to match new to old based on datatype
    for newNameType in newNameTypes.copy():
        matchedOldNameTypes = [oldNameType for oldNameType in oldNameTypes if oldNameType[1] == newNameType[1]]
        if matchedOldNameTypes:
            matchedNames.append((newNameType[0], matchedOldNameTypes[0][0]))
            newNameTypes.remove(newNameType)
            oldNameTypes.remove(matchedOldNameTypes[0])

    # Match any remaining ones in order
    for newNameType in reversed(newNameTypes):
        if oldNameTypes:
            matchedOldNameType = oldNameTypes.pop()
            matchedNames.append((newNameType[0], matchedOldNameType[0]))
            newNameTypes.remove(newNameType)
            oldNameTypes.remove(matchedOldNameType)

    # Add any new ones to the list
    oldNames = [oldNameType[0] for oldNameType in oldNameTypes]
    newNames = [newNameType[0] for newNameType in newNameTypes]

    return matchedNames, newNames, oldNames


def SyncPorts(block: BaseLogicBlock, inputPortsDict: Dict[str, Tuple[Union[Type, List, None], Any]],
              outputPortsDict: Dict[str, Union[Type, List, None]]):
    newInputNameTypes = [(name, inputPortsDict[name][0]) for name in inputPortsDict.keys()]
    oldInputNameTypes = [(inputPort.name, inputPort.dataType) for inputPort in block.GetInputPorts()]
    (matchedInputPortNames, newInputPortNames, oldInputPortNames) = MatchNamesAndTypes(newInputNameTypes,
                                                                                       oldInputNameTypes)

    newOutputNameTypes = [(name, outputPortsDict[name][0]) for name in outputPortsDict.keys()]
    oldOutputNameTypes = [(outputPort.name, outputPort.dataType) for outputPort in block.GetOutputPorts()]
    (matchedOutputPortNames, newOutputPortNames, oldOutputPortNames) = MatchNamesAndTypes(newOutputNameTypes,
                                                                                          oldOutputNameTypes)

    for (newPortName, oldInputPortName) in matchedInputPortNames:
        oldPort = [inputPort for inputPort in block.GetInputPorts() if inputPort.name == oldInputPortName]
        oldPort[0].name = newPortName
        oldPort[0].dataType = inputPortsDict[newPortName][0]
        oldPort[0].SetDefaultValue(inputPortsDict[newPortName][1])

    for (newPortName, oldInputPortName) in matchedOutputPortNames:
        oldPort = [outputPort for outputPort in block.GetOutputPorts() if outputPort.name == oldInputPortName]
        oldPort[0].name = newPortName
        oldPort[0].dataType = outputPortsDict[newPortName]

    for oldInputPortName in oldInputPortNames:
        block.RemovePort([port for port in block.GetInputPorts() if port.name == oldInputPortName][0])

    for oldOutputPortName in oldOutputPortNames:
        block.RemovePort([port for port in block.GetOutputPorts() if port.name == oldOutputPortName][0])

    for newPortName in newInputPortNames:
        block.CreateInputPort(newPortName, inputPortsDict[newPortName][0], inputPortsDict[newPortName][1])

    for newPortName in newOutputPortNames:
        block.CreateOutputPort(newPortName, outputPortsDict[newPortName])


def SyncParameters(block: BaseLogicBlock, parametersDict: Dict[str, Tuple[Union[Type, List, None], Any]]):
    newNameTypes = [(name, parametersDict[name][0]) for name in parametersDict.keys()]
    oldNameTypes = [(parameter.name, parameter.dataType) for parameter in block.GetParameters()]
    (matchedParameterNames, newParameterNames, oldParameterNames) = MatchNamesAndTypes(newNameTypes, oldNameTypes)

    for (newParameterName, oldParameterName) in matchedParameterNames:
        oldParameter = [parameter for parameter in block.GetParameters() if parameter.name == oldParameterName]
        oldParameter[0].name = newParameterName
        if oldParameter[0].dataType != parametersDict[newParameterName][0]:
            oldParameter[0].dataType = parametersDict[newParameterName][0]
            oldParameter[0].SetValue(parametersDict[newParameterName][1])

    for oldParameterName in oldParameterNames:
        block.RemoveParameter(
            [parameter for parameter in block.GetParameters() if parameter.name == oldParameterName][0])

    for newParameterName in newParameterNames:
        block.CreateParameter(newParameterName, parametersDict[newParameterName][0],
                              parametersDict[newParameterName][1])
