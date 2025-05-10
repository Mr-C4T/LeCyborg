"""
1) Scan for BL devices MAC :
hcitool scan
2) Edit LeCyborg-connect.sh with esp32 mac and LeCyborg-client.py args
nano LeCyborg-connect.sh

to test activation values use --test:
python LeCyborg-client.py --test --mean --mean-window 50 --threshold 600

Once you found values that allow you to easily start/stop you can try to controll inference :
sudo phosphobot run --no-cameras
python server.py --model_id MrC4t/Test-ACT-2
python LeCyborg-client.py --mean --camera-ids 5 6
"""

import argparse
import time
import numpy as np
import serial
from phosphobot.camera import AllCameras
from phosphobot.api.client import PhosphoApi
from phosphobot.am import ACT
from collections import deque

def parse_args():
    parser = argparse.ArgumentParser(description="Control ACT inference with MyoWare sensor.")
    parser.add_argument('--threshold', type=int, default=600, help="Threshold for triggering inference")
    parser.add_argument('--camera-ids', type=int, nargs='+', default=[5, 6], help="List of camera IDs to use")
    parser.add_argument('--mean', action='store_true', help="Use mean of sensor values instead of latest")
    parser.add_argument('--mean-window', type=int, default=50, help="Window size for mean filtering")
    parser.add_argument('--port', type=str, default='/dev/rfcomm0', help="Serial port for MyoWare (e.g., COM5 or /dev/rfcomm0)")
    parser.add_argument('--baudrate', type=int, default=115200, help="Serial baud rate")
    parser.add_argument('--test', action='store_true', help="Disable inference and just print sensor values")
    return parser.parse_args()

def main():
    args = parse_args()

    client = PhosphoApi(base_url="http://localhost:8020")
    allcameras = AllCameras()
    model = ACT()
    sensor_values = deque(maxlen=args.mean_window)

    try:
        with serial.Serial(args.port, args.baudrate, timeout=0) as bt_serial:
            print(f"✅ Connected to {args.port} at {args.baudrate} baud. 📡")
            time.sleep(2.0)  # Allow sensors/cameras to warm up

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
                        print("🟢")
                        if not args.test:
                            images = [
                                allcameras.get_rgb_frame(cam_id, resize=(320, 240))
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
                        print("🔴")

    except serial.SerialException as e:
        print(f"❌ Failed to connect: {e}")
    except KeyboardInterrupt:
        print("Exiting gracefully.")

if __name__ == "__main__":
    main()
