import argparse
import time
import numpy as np
import serial
from phosphobot.api.client import PhosphoApi
from collections import deque

def parse_args():
    parser = argparse.ArgumentParser(description="Control gripper using MyoWare sensor.")
    parser.add_argument('--threshold', type=int, default=600, help="Threshold for flex detection")
    parser.add_argument('--mean', action='store_true', help="Use mean of sensor values")
    parser.add_argument('--mean-window', type=int, default=50, help="Size of rolling filter")
    parser.add_argument('--port', type=str, default='/dev/rfcomm0', help="Serial port for MyoWare sensor")
    parser.add_argument('--baudrate', type=int, default=115200, help="Serial baud rate")
    parser.add_argument('--phospho-url', type=str, default='http://localhost:80', help="Phospho control server URL")
    parser.add_argument('--test', action='store_true', help="Just print sensor values")
    return parser.parse_args()

def main():
    args = parse_args()

    sensor_values = deque(maxlen=args.mean_window)
    client = PhosphoApi(base_url=args.phospho_url)

    gripper_open = False  # track current state

    try:
        with serial.Serial(args.port, args.baudrate, timeout=0) as bt_serial:
            print(f"📡 Connected to {args.port} at {args.baudrate} baud.")
            time.sleep(2.0)

            # Move to a default position
            print("🦾 Moving robot to default position...")
            client.move.absolute(x=0, y=0, z=30, speed=0.5)
            time.sleep(2)

            print("✅ Ready. Flex muscle to control gripper!")

            while True:
                latest_line = None
                while bt_serial.in_waiting:
                    latest_line = bt_serial.readline().decode('utf-8', errors='replace').strip()

                if latest_line and latest_line.isdigit():
                    value = int(latest_line)
                    sensor_values.append(value)
                    filtered_val = np.mean(sensor_values) if args.mean else value
                    print(f"Sensor value: {value} | Filtered: {filtered_val:.1f} | Threshold: {args.threshold}", end=" ")

                    if filtered_val > args.threshold:
                        print("🟢 Flex detected!")

                        if not args.test:
                            gripper_open = not gripper_open
                            grip_val = 1.0 if gripper_open else 0.0
                            client.move.gripper(grip_val)
                            print(f"→ Gripper {'opened' if gripper_open else 'closed'}")
                            time.sleep(1.0)  # debounce delay
                    else:
                        print("🔴")

    except serial.SerialException as e:
        print(f"❌ Serial error: {e}")
    except KeyboardInterrupt:
        print("👋 Exiting gracefully.")

if __name__ == "__main__":
    main()
