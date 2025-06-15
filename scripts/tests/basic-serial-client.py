import serial
import time

BLUETOOTH_PORT = '/dev/rfcomm0'  # Change this if needed (win=COM5)
BAUD_RATE = 115200

try:
    with serial.Serial(BLUETOOTH_PORT, BAUD_RATE, timeout=0) as bt_serial:
        print(f"Connected to {BLUETOOTH_PORT} at {BAUD_RATE} baud.")
        while True:
            latest_line = None
            while bt_serial.in_waiting:
                latest_line = bt_serial.readline().decode('utf-8', errors='replace').strip()

            if latest_line:
                print(f"> {latest_line}")

            time.sleep(1 / 30)  # ~33ms delay for ~30Hz loop
except serial.SerialException as e:
    print(f"Failed to connect: {e}")
except KeyboardInterrupt:
    print("Exiting...")
