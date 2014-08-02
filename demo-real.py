import rayled
import serial
rayled.s = serial.Serial("/dev/ttyUSB0", 38400)
rayled.main()
