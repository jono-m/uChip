class Test:
    def __init__(self, something: str):
        self._something = something

    def __eq__(self, other):
        if isinstance(other, Test):
            return self._something == other._something

a = Test("a")
b = Test("b")
c = Test("a")

exList = [b]

print(c in exList)
