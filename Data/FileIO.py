import dill
from pathlib import Path


def LoadObject(path: Path):
    file = open(path, "rb")
    obj = dill.load(file)
    file.close()
    return obj


def SaveObject(obj, path: Path):
    file = open(path, "wb+")
    dill.dump(obj, file)
    file.close()
