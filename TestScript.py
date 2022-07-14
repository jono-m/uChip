from ucscript import *

valve = Parameter(Valve)


def RunProgram():
    valve.Get().SetOpen(False)
