script = """
import math
def Test():
    print(math.floor(1.5))
"""

# Fill the globals dictionary
globalsDict = {}
exec("", globalsDict)

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
globalsDict['Test']()
