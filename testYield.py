from Model.Program.Program import Program
import types


def SomeFunction():
    for i in range(5):
        yield SomeFunction()


test = SomeFunction()

while True:
    value = next(test, None)
    if value is not None:
        print(value)
    else:
        break
