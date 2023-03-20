def A():
    yield 2
    yield 4


def B():
    yield from A()
    yield 4


for x in B():
    print(x)
