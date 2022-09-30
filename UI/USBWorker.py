import threading
import time
from UI.UIMaster import UIMaster


class USBWorker:
    def __init__(self):
        self.thread = threading.Thread(target=self.Loop, daemon=True)
        self.doStop = False
        self.thread.start()

    def Loop(self):
        while not self.doStop:
            UIMaster.Instance().rig.RescanForDevices()
            time.sleep(1)
