from serial.tools.list_ports import comports

foundDevices = comports()

print(["%s (%s) - %s" % (x.name, x.device, x.description) for x in foundDevices])