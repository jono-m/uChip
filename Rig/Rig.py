from Util import *
from Rig.Device import Device
from typing import List
import typing
import pickle
import os


class DeviceSetting:
    def __init__(self, priority, invertA, invertB, invertC):
        self.priority = priority
        self.invertA = invertA
        self.invertB = invertB
        self.invertC = invertC


class Rig:
    def __init__(self):
        super().__init__()
        self._connectedDevices: List[Device] = []
        self.OnFlush = Event()

        self.deviceSettings: typing.Dict[str, DeviceSetting] = {}

        self.solenoidStates = []

        self.lastSolenoidStates = []

        self.drivenSolenoids = []

        self.lastDrivenSolenoids = []

        self.ReconnectAll()

    def GetConnectedDevices(self):
        return self._connectedDevices[:]

    def ReconnectAll(self):
        self.DisconnectAll()

        # Connect to all devices
        for port in Device.FindConnectedDevices():
            newDevice = Device(port)
            newDevice.Connect()

            self._connectedDevices.append(newDevice)

        # Load all device settings from memory
        self.ReloadDeviceSettings()

        # For all device settings that aren't in memory yet, create them
        self.EnsureDeviceSettings()

        # Make sure we have enough states for these devices.
        self.EnsureSolenoids(len(self._connectedDevices) * 24)

        # Make sure the devices are in order in the list
        self.ResortDevices()

        # Push the current states to the devices
        self.Flush()

    def EnsureSolenoids(self, number):
        numToAdd = number - len(self.solenoidStates)
        self.solenoidStates += [False] * numToAdd
        self.solenoidStates = self.solenoidStates[:number]

    def DisconnectAll(self):
        for device in self._connectedDevices:
            device.Disconnect()

        self._connectedDevices = []

    def ReloadDeviceSettings(self):
        if os.path.exists("devicePreferences.pkl"):
            file = open("devicePreferences.pkl", "rb")
            self.deviceSettings = pickle.load(file)
            file.close()
        else:
            self.deviceSettings = {}

    def EnsureDeviceSettings(self):
        # Get highest priority in settings list
        priorities = [setting.priority for setting in self.deviceSettings.values()]

        if len(priorities) == 0:
            maxPriority = -1
        else:
            maxPriority = max(priorities)

        for device in self._connectedDevices:
            if device.portInfo.serial_number not in self.deviceSettings:
                self.deviceSettings[device.portInfo.serial_number] = DeviceSetting(maxPriority + 1, False, False, False)
                maxPriority += 1

        self.SaveDeviceSettings()

    def SaveDeviceSettings(self):
        file = open("devicePreferences.pkl", "wb")
        pickle.dump(self.deviceSettings, file)
        file.close()

    def ResortDevices(self):
        self._connectedDevices.sort(key=lambda x: self.deviceSettings[x.portInfo.serial_number].priority)

    def Promote(self, device: Device):
        if device is None or len(self._connectedDevices) == 0:
            return

        try:
            deviceIndex = self._connectedDevices.index(device)
        except ValueError:
            return

        # Can't promote past end
        if deviceIndex == len(self._connectedDevices) - 1:
            return

        myPriority = self.deviceSettings[device.portInfo.serial_number].priority
        nextDevice = self._connectedDevices[deviceIndex + 1]
        nextPriority = self.deviceSettings[nextDevice.portInfo.serial_number].priority
        self.deviceSettings[nextDevice.portInfo.serial_number].priority = myPriority
        self.deviceSettings[device.portInfo.serial_number].priority = nextPriority

        self.SaveDeviceSettings()

        self.ResortDevices()
        self.Flush()

    def Demote(self, device: Device):
        if device is None or len(self._connectedDevices) == 0:
            return

        try:
            deviceIndex = self._connectedDevices.index(device)
        except ValueError:
            return

        # Can't demote before beginning
        if deviceIndex == 0:
            return

        myPriority = self.deviceSettings[device.portInfo.serial_number].priority
        previousDevice = self._connectedDevices[deviceIndex - 1]
        nextPriority = self.deviceSettings[previousDevice.portInfo.serial_number].priority
        self.deviceSettings[previousDevice.portInfo.serial_number].priority = myPriority
        self.deviceSettings[device.portInfo.serial_number].priority = nextPriority

        self.SaveDeviceSettings()

        self.ResortDevices()
        self.Flush()

    def IsSolenoidOn(self, number):
        if number >= len(self.solenoidStates):
            return False
        return self.solenoidStates[number]

    def SetSolenoid(self, number, isOn):
        if number >= len(self.solenoidStates):
            return
        self.solenoidStates[number] = isOn

    def Flush(self):
        if self.lastSolenoidStates == self.solenoidStates and \
                self.lastDrivenSolenoids == self.drivenSolenoids:
            return
        else:
            self.lastSolenoidStates = self.solenoidStates[:]
            self.lastDrivenSolenoids = self.drivenSolenoids
        print(self.solenoidStates[:30])
        # propagates solenoid state changes upwards to the delegate and down to the devices
        # the device list should always be sorted by priority at this point.
        for deviceIndex in range(len(self._connectedDevices)):
            device = self._connectedDevices[deviceIndex]
            solenoidIndexStart = deviceIndex * 24
            solenoidIndexEnd = solenoidIndexStart + 24
            states = self.ApplyInversion(self.solenoidStates[solenoidIndexStart:solenoidIndexEnd],
                                         self.deviceSettings[device.portInfo.serial_number].invertA,
                                         self.deviceSettings[device.portInfo.serial_number].invertB,
                                         self.deviceSettings[device.portInfo.serial_number].invertC)
            device.Flush(states)

        self.OnFlush.Invoke()

    def GetDeviceInversion(self, serNo):
        return (self.deviceSettings[serNo].invertA,
                self.deviceSettings[serNo].invertB,
                self.deviceSettings[serNo].invertC)

    def SetDeviceInversion(self, serNo, invertA, invertB, invertC):
        self.deviceSettings[serNo].invertA = invertA
        self.deviceSettings[serNo].invertB = invertB
        self.deviceSettings[serNo].invertC = invertC
        self.SaveDeviceSettings()
        self.Flush()

    @staticmethod
    def ApplyInversion(states, invertA, invertB, invertC):
        return [state ^ invertA for state in states[0:8]] + \
               [state ^ invertB for state in states[8:16]] + \
               [state ^ invertC for state in states[16:24]]
