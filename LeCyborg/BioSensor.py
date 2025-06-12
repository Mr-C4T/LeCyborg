import serial
import time
import threading


# BLUETOOTH_PORT = '/dev/rfcomm0'  # Change this if needed (win=COM5)
# BAUD_RATE = 115200

class BioSensor(threading.Thread):
    """
    Sensor based on an ESP32.
    """
    def __init__(self, port, baudrate = 115200):
        """
        ensor based on an ESP32


        params:
        - port : str -> port of the serial or bt_serial device
        - baudrate : int (default 115200) -> baudrate of serial or bt_serial
        """
        threading.Thread.__init__( self )
        self.port = port
        self.baudrate = baudrate
        self.device = None
        self.last_value = None
        self.connected = False
        self.disconnect_request = threading.Event()
        pass

    def run(self):
        while self.connected:
            self.last_value = self.read()
            time.sleep(1 / 30)  # ~33ms delay for ~30Hz loop

            if self.disconnect_request.is_set():
                self.connected = False

    def get_last_value(self):
        return self.last_value

    def connect(self):
        """
        init the connection with the sensor device
        """
        try:
            self.device = serial.Serial(self.port, self.baudrate, timeout=0)
            self.connected = True
        except Exception as e:
            print(f"ERROR: BioSensor.connect() :{e}")

    def read(self):
        """
        will return the value read by the sensor
        """
        try:
            latest_line = None
            while self.device.in_waiting:
                latest_line = self.device.readline().decode('utf-8', errors='replace').strip()

            if latest_line:
                return float(latest_line)
            else:
                return None
            

        except Exception as e:
            print(f"ERROR: BioSensor.read() :{e}")
    
    def disconnect(self):
        self.disconnect_request.set()
