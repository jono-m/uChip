from ucscript import *

valveNumber = Parameter(int)
pwmFraction = Parameter(float, minimum=0, maximum=100)
frequency = Parameter(float)

def SetValves(v, r):
    FindValve("V" + str(valveNumber.Get())).SetOpen(v)
    FindValve("R" + str(valveNumber.Get())).SetOpen(r)

@display
def On():
    SetValves(False, True)

@display
def Off():
    SetValves(True, False)

@display
def PWM():
    v = FindValve("V" + str(valveNumber.Get()))
    r = FindValve("R" + str(valveNumber.Get()))
    i = 0
    while True:
        frac = pwmFraction.Get()/100.0
        f = frequency.Get()
        if f == 0:
            period = 1
        else:
            period = 1.0/f
        
        secOn = period*frac
        secOff = period*(1-frac)
        if secOff > 0:
            v.SetOpen(True)
            r.SetOpen(False)
            yield WaitForSeconds(secOff)
        if secOn > 0:
            v.SetOpen(False)
            r.SetOpen(True)
            yield WaitForSeconds(secOn)        
        i += 1
        Log("Cycle " + str(i) + " completed")
        if i == 10:
            Log(test)