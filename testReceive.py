import time

import serial


def BytesToPinStates(d: bytes):
    a = reversed([int(x) for x in bin(d[1])[2:].zfill(8)])
    b = reversed([int(x) for x in bin(d[3])[2:].zfill(8)])
    c = reversed([int(x) for x in bin(d[5])[2:].zfill(8)])
    return list(a) + list(b) + list(c)


def ProfileToggle():
    with serial.Serial("COM2", timeout=None) as s:
        lastTime = time.time()
        lastState = False
        while True:
            l = s.read(6)
            states = BytesToPinStates(l)
            state = bool(states[15])
            if state != lastState:
                t = time.time()
                print("TOGGLED: " + str(t - lastTime))
                lastTime = t
            lastState = state


def ProfileSend():
    with serial.Serial("COM2", timeout=None) as s:
        lastTime = time.time()
        i = 0
        while True:
            l = s.read(6)
            t = time.time()
            i += 1
            if i % 10 == 0:
                print(t - lastTime)
                i = 0
            lastTime = t


ProfileToggle()
