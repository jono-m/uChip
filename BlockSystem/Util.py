import typing


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
