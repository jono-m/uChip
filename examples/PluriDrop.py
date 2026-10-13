from ucscript import *

class Chip: 
    def __init__(self):
        self.reagentValves = [FindValve("R"+str(i+1)) for i in range(8)]
        self.vehicleValves = [FindValve("V"+str(i+1)) for i in range(8)]
        self.sampleValve = FindValve("Sample")
        self.oilValve = FindValve("Oil")
        self.keepValve = FindValve("Keep")
        self.discardValve = FindValve("Discard")
        self.allValves = self.reagentValves+self.vehicleValves+[self.sampleValve,self.oilValve,self.keepValve,self.discardValve]

@display("Full Seal")
def FullSeal():
    chip = Chip()
    [valve.Close() for valve in chip.allValves]

@display("Close All Inlets")
def CloseAllInlets():
    chip = Chip()
    [valve.Close() for valve in chip.allValves]
    chip.discardValve.Open()


@display("Flush Vehicles")
def FlushVehicles():
    chip = Chip()
    [valve.Close() for valve in chip.allValves]
    chip.discardValve.Open()
    [valve.Open() for valve in chip.vehicleValves]

@display("Debubble")
def Debubble():
    chip = Chip()
    [valve.Close() for valve in chip.allValves]
    chip.discardValve.Open()
    chip.vehicleValves[0].Open()
    yield WaitForSeconds(2)
    chip.discardValve.Close()

@display("Sample Droplet Calibration")
def SampleDropletCalibration():
    chip = Chip()
    [valve.Close() for valve in chip.allValves]
    chip.sampleValve.Open()
    chip.oilValve.Open()
    chip.discardValve.Open()


@display("Droplet Calibration")
def DropletCalibration():
    chip = Chip()
    [valve.Close() for valve in chip.allValves]
    chip.sampleValve.Open()
    chip.oilValve.Open()
    chip.discardValve.Open()
    [valve.Open() for valve in chip.vehicleValves]


valveCloseDelay = Parameter(float)
conditionStabilizeTime = Parameter(float)
dropletStabilizeTime = Parameter(float)
def SwitchCondition(doSwitch):
    chip = Chip()
    chip.discardValve.Open()
    yield WaitForSeconds(valveCloseDelay.Get())
    chip.keepValve.Close()
    chip.oilValve.Close()
    doSwitch()
    yield WaitForSeconds(conditionStabilizeTime.Get())
    chip.oilValve.Open()
    yield WaitForSeconds(dropletStabilizeTime.Get())
    chip.keepValve.Open()
    yield WaitForSeconds(valveCloseDelay.Get())
    chip.discardValve.Close()


@display
def CA():
    rgtA = FindProgram("REAGENT 1")
    rgtB = FindProgram("REAGENT 2")
    def SelA():
        rgtA.On()
    yield from SwitchCondition(SelA)

@display
def CB():
    rgtA = FindProgram("REAGENT 1")
    rgtB = FindProgram("REAGENT 2")
    def SelB():
        rgtA.Off()
    yield from SwitchCondition(SelB)

@display
def Keep():
    chip = Chip()
    chip.keepValve.Open()
    yield WaitForSeconds(valveCloseDelay.Get())
    chip.discardValve.Close()

@display
def RunSwitchingExperiment():
    rgtA = FindProgram("REAGENT 1")
    rgtB = FindProgram("REAGENT 2")
    def SelA():
        rgtA.On()
    def SelB():
        rgtA.Off()
    while True:
        yield from SwitchCondition(SelA)
        yield WaitForSeconds(2)
        yield from SwitchCondition(SelB)
        yield WaitForSeconds(2)


@display
def RunCollectionExperiment():
    rgts = [FindProgram("REAGENT " + str(i)) for i in range(1, 9)]
    chip = Chip()
    for reagent in rgts:
        #Turn on collection
        DropletCalibration()
        reagent.On()
        #Stabilize
        yield WaitForSeconds(1)

        #Collect
        chip.keepValve.Open()
        yield WaitForSeconds(valveCloseDelay.Get())
        chip.discardValve.Close()
        yield WaitForSeconds(60)
        
        #Flush
        CloseAllInlets()
        chip.keepValve.Open()
        chip.discardValve.Close()
        chip.oilValve.Open()
        yield WaitForSeconds(20)
        chip.discardValve.Open()
        yield WaitForSeconds(valveCloseDelay.Get())
    CloseAllInlets()