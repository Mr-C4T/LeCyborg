import argparse
import time
import numpy as np
import serial
import requests
from collections import deque

BASE_URL = "http://localhost:80"

def parse_args():
    parser = argparse.ArgumentParser(description="Control Phosphobot gripper with MyoWare sensor.")
    parser.add_argument('--threshold', type=int, default=600, help="Activation threshold")
    parser.add_argument('--mean', action='store_true', help="Use moving average")
    parser.add_argument('--mean-window', type=int, default=50, help="Moving average window size")
    parser.add_argument('--port', type=str, default='/dev/rfcomm0', help="Serial port for ESP32")
    parser.add_argument('--baudrate', type=int, default=115200, help="Baudrate for serial")
    parser.add_argument('--test', action='store_true', help="Test sensor values only")
    return parser.parse_args()

def move_gripper(open_val):
    """Send move/absolute command with updated gripper open value."""
    payload = {
        "x": -15, "y": 0, "z": 0,
        "rx": 0, "ry": 0, "rz": 0,
        "open": open_val,
        "max_trials": 10,
        "position_tolerance": 0.03,
        "orientation_tolerance": 0.2
    }
    try:
        requests.post(f"{BASE_URL}/move/absolute", json=payload, timeout=1)
        print(f"🦾 Gripper {'OPEN' if open_val > 0.5 else 'CLOSED'}")
    except requests.RequestException as e:
        print(f"❌ Gripper move failed: {e}")

def main():
    args = parse_args()

    # Step 1: Init robot
    try:
        print("🟢 Initializing robot...")
        requests.post(f"{BASE_URL}/move/init", timeout=2).raise_for_status()
        print("✅ Robot initialized.")
    except requests.RequestException as e:
        print(f"❌ Init failed: {e}")
        return

    # Step 2: Move to default position (closed)
    move_gripper(open_val=0)

    # Step 3: Read sensor
    sensor_values = deque(maxlen=args.mean_window)
    try:
        with serial.Serial(args.port, args.baudrate, timeout=0) as bt_serial:
            print(f"📡 Connected to {args.port} at {args.baudrate} baud.")
            current_state = None  # Track current gripper state

            while True:
                line = None
                while bt_serial.in_waiting:
                    line = bt_serial.readline().decode("utf-8", errors="replace").strip()

                if line and line.isdigit():
                    value = int(line)
                    sensor_values.append(value)
                    filtered = np.mean(sensor_values) if args.mean else value

                    print(f"💪 Sensor: {value} | Filtered: {filtered:.1f} | Threshold: {args.threshold}", end=" ")

                    if args.test:
                        print()
                        continue

                    desired_state = 0 if filtered > args.threshold else 1  # close if > threshold

                    if current_state != desired_state:
                        move_gripper(open_val=desired_state)
                        current_state = desired_state
                    else:
                        print("⏸️ No change")
                time.sleep(0.01)

    except serial.SerialException as e:
        print(f"❌ Serial connection failed: {e}")
    except KeyboardInterrupt:
        print("\n👋 Exiting.")

if __name__ == "__main__":
    main()

