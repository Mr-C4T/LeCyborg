"""
Script for ACT inference control using Phosphobot and ESP32 + MyoWare sensor as a trigger.

🧠 Workflow:

1️⃣ Scan for Bluetooth MAC address of your ESP32:
    hcitool scan

2️⃣ Edit the connection script with MAC + args:
    nano LeCyborg-connect.sh
    sudo chmod +x LeCyborg-connect.sh

3️⃣ Run connection + inference loop:
    bash LeCyborg-connect.sh

🧪 Test sensor readings only:
    python LeCyborg-client.py --test --mean --mean-window 50 --threshold 600

🧠 Trigger ACT model inference:
    sudo phosphobot run --no-cameras
    python phosphobot/inference/ACT/server.py --model_id MrC4t/Test-ACT-2
    python LeCyborg-client.py --mean --camera-ids 5 6

"""

import argparse
import time
import numpy as np
import serial
from collections import deque
from phosphobot.api.client import PhosphoApi
from phosphobot.camera import AllCameras
from phosphobot.am import ACT

def parse_args():
    parser = argparse.ArgumentParser(description="Control ACT inference with MyoWare sensor.")
    parser.add_argument('--threshold', type=int, default=600, help="Threshold for triggering inference")
    parser.add_argument('--camera-ids', type=int, nargs='+', default=[5, 6], help="List of camera IDs to use")
    parser.add_argument('--mean', action='store_true', help="Use mean of sensor values instead of raw value")
    parser.add_argument('--mean-window', type=int, default=50, help="Size of the rolling average window")
    parser.add_argument('--port', type=str, default='/dev/rfcomm0', help="Serial port for MyoWare (e.g., /dev/rfcomm0)")
    parser.add_argument('--baudrate', type=int, default=115200, help="Serial baud rate")
    parser.add_argument('--phospho-url', type=str, default='http://localhost:80', help="Phospho control server URL")
    parser.add_argument('--test', action='store_true', help="Disable inference and just print sensor values")
    return parser.parse_args()

def main():
    args = parse_args()

    sensor_values = deque(maxlen=args.mean_window)
    client = PhosphoApi(base_url=args.phospho_url)
    cameras = AllCameras()
    model = ACT()

    try:
        with serial.Serial(args.port, args.baudrate, timeout=0) as bt_serial:
            print(f"📡 Listening on {args.port} @ {args.baudrate} baud.")

            while True:
                latest_line = None
                while bt_serial.in_waiting:
                    latest_line = bt_serial.readline().decode('utf-8', errors='replace').strip()

                if latest_line and latest_line.isdigit():
                    value = int(latest_line)
                    sensor_values.append(value)
                    filtered_val = np.mean(sensor_values) if args.mean else value
                    print(f"Sensor: {value} | Filtered: {filtered_val:.1f} | Threshold: {args.threshold}", end=" ")

                    if filtered_val > args.threshold:
                        print("🟢 Triggered")
                        if not args.test:
                            images = [
                                cameras.get_rgb_frame(cam_id, resize=(320, 240))
                                for cam_id in args.camera_ids
                            ]
                            state = client.control.read_joints()
                            actions = model({
                                "state": np.array(state.angles_rad),
                                "images": np.array(images)
                            })

                            for action in actions:
                                client.control.write_joints(angles=action.tolist())
                                time.sleep(1 / 30)
                    else:
                        print("🔴 Idle")

    except serial.SerialException as e:
        print(f"❌ Serial error: {e}")
    except KeyboardInterrupt:
        print("👋 Interrupted. Exiting.")

if __name__ == "__main__":
    main()
