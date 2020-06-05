from Util import *


class Test:
    def __init__(self):
        self.data = "Hello!"
        self.DoThing = Event()

    def __del__(self):
        print("Deleted")


def PrintYello():
    print("Yello")


test = Test()
test.DoThing.Register(PrintYello)

testCpy = test

test.DoThing.Invoke()

del test

print("End")
