from ucscript import *

valves = Parameter(ListParameter(Valve), "Valves")
valveTest = Parameter(float)


def OpenAll():
    [v.Open() for v in valves.Get()]


def CloseAll():
    [v.Close() for v in valves.Get()]
