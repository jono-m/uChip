## This is the color generator script.

class Chip:
    def __init__(self):
        self.cyans = [FindValve("R" + str(x)) for x in range(8)]
        self.cyans_v = [FindValve("V" + str(x)) for x in range(8)]

        self.magentas = [FindValve("R" + str(x + 8)) for x in range(8)]
        self.magentas_v = [FindValve("V" + str(x + 8)) for x in range(8)]

        self.yellows = [FindValve("R" + str(x + 16)) for x in range(8)]
        self.yellows_v = [FindValve("V" + str(x + 16)) for x in range(8)]

        self.keys = [FindValve("R" + str(x + 24)) for x in range(8)]
        self.keys_v = [FindValve("V"+str(x+24)) for x in range(8)]

        self.keep = FindValve("Keep")
        self.discard = FindValve("Discard")
        self.oil = FindValve("Oil")
        self.sample = FindValve("Sample")

        self.flattened = [self.keep, self.discard, self.oil, self.sample]
        self.flattened += self.cyans + self.cyans_v
        self.flattened += self.magentas + self.magentas_v
        self.flattened += self.yellows + self.yellows_v
        self.flattened += self.keys + self.keys_v

        self.vehicles = self.cyans_v + self.magentas_v + self.yellows_v + self.keys_v
        self.dyes = self.cyans + self.magentas + self.yellows + self.keys

def CloseAll():
    chip = Chip()
    [v.Close() for v in chip.flattened]
    chip.keep.Open()

def StartGeneration():
    chip = Chip()
    
    [v.Close() for v in chip.dyes]
    [v.Open() for v in chip.vehicles]
    chip.oil.Close()
    chip.discard.Close()
    chip.keep.Open()
    chip.sample.Open()
    yield WaitForSeconds(1)
    chip.oil.Open()

def SetColor(c, m, y, k):
    cyan = [bool(x == '1') for x in format(c, '08b')]
    magenta = [bool(x == '1') for x in format(m, '08b')]
    yellow = [bool(x == '1') for x in format(y, '08b')]
    key = [bool(x == '1') for x in format(k, '08b')]
    chip = Chip()
    [[c.SetOpen(x), v.SetOpen(not x)] for (c, v, x) in zip(chip.cyans, chip.cyans_v, cyan)]
    [[c.SetOpen(x), v.SetOpen(not x)] for (c, v, x) in zip(chip.magentas, chip.magentas_v, magenta)]
    [[c.SetOpen(x), v.SetOpen(not x)] for (c, v, x) in zip(chip.yellows, chip.yellows_v, yellow)]
    [[c.SetOpen(x), v.SetOpen(not x)] for (c, v, x) in zip(chip.keys, chip.keys_v, key)]


def PollColor():
    path = r"C:/Users/jonoj/Repositories/uChip/uchipconduit.txt"
    open(path, "w").close()
    file = open(path, "r")
    while True:
        text = file.readline()
        s = text.strip().split(',')
        if len(s) == 4:
            c, m, y, k = [int(x) for x in s]
            SetColor(c, m, y, k)
        else:
            yield WaitForSeconds(0.1)

from PySide6.QtWidgets import QColorDialog

def ColorPicker():
    msgBox = QColorDialog()
    msgBox.currentColorChanged.connect(UpdateColor)
    msgBox.exec()

def UpdateColor(color):
    SetColorRGB(color.red(), color.green(), color.blue())