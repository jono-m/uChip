import serial
import sys

portToOpen = sys.argv[1]

port = serial.Serial(portToOpen)

while True:
    line = input("Line")
    port.write(line.encode())
