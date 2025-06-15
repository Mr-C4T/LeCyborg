from BioSensor import BioSensor
import time


sensor = BioSensor("/dev/rfcomm0")
#sensor = BioSensor("/dev/ttyUSB0")
sensor.connect()
time.sleep(1/30)
sensor.start()

try:
    while True:
        print(sensor.get_last_value())
except KeyboardInterrupt as e:
    sensor.disconnect()
