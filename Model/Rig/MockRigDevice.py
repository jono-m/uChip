from Model.Rig.RigDevice import RigDevice


class MockRigDevice(RigDevice):
    def Write(self, data: bytes):
        if self.isConnected:
            print(data)

    def Connect(self):
        self.isConnected = True
        print("Connected.")

    def IsDeviceAvailable(self) -> bool:
        return True

    def Disconnect(self):
        self.isConnected = False
        print("Disconnected")
