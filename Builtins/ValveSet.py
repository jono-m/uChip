from ucscript import *

valves = Parameter(ListParameter(Valve), "Valves")
valveTest = Parameter(float)

@display
def OpenAll():
    [v.Open() for v in valves.Get()]

@display
def CloseAll():
    [v.Close() for v in valves.Get()]
