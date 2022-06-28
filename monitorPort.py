import serial
import sys

portToOpen = sys.argv[1]

port = serial.Serial(portToOpen, timeout=0)

while True:
    line = port.read()
    if line:
        print(line)
