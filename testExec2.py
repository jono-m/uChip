script = """
import math
a = 1
def Test():
    print(math.floor(1.5))
"""
from enum import Enum
class A:
    def __init__(self):
        self.a = 1
# Fill the globals dictionary
globalsDict = {}
exec("", globalsDict)
print(globalsDict['__builtins__']['A'])
# Replace the importer
standardImporter = globalsDict['__builtins__']['__import__']

class Namespace:
    @staticmethod
    def floor(val):
        return val*2

def ImportInterceptor(name, *args, **kwargs):
    if name == "math":
        return Namespace
    else:
        return standardImporter(name, *args, **kwargs)


globalsDict['__builtins__']['__import__'] = ImportInterceptor
exec(script, globalsDict)
# globalsDict['Test']()
