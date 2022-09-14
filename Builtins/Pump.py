from ucscript import *

cyclesPerSecond = Parameter(float)
pumpValveA = Parameter(Valve)
pumpValveB = Parameter(Valve)
pumpValveC = Parameter(Valve)
pumpValves = [pumpValveA, pumpValveB, pumpValveC]
pattern = [(0, 0, 0),
           (1, 0, 0),
           (1, 1, 0),
           (0, 1, 0),
           (0, 1, 1),
           (0, 0, 1)]


@hidden
def ClosePump():
    [valve.Get().SetOpen(False) for valve in pumpValves]


@onStop(ClosePump)
@onPause(ClosePump)
def RunPump():
    i = 0
    while True:
        [valve.Get().SetOpen(bool(state)) for (valve, state) in zip(pumpValves, pattern[i])]
        yield WaitForSeconds(1 / cyclesPerSecond.Get())
        i = (i + 1) % len(pattern)
