# sudo chmod 777 /dev/rfcomm0 

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
    parser.add_argument('--threshold', type=int, default=1500, help="Threshold for triggering inference")
    parser.add_argument('--camera-ids', type=int, nargs='+', default=[0, 1], help="List of camera IDs to use")
    parser.add_argument('--mean', action='store_true', help="Use mean of sensor values instead of latest")
    parser.add_argument('--mean-window', type=int, default=5, help="Window size for mean filtering")
    parser.add_argument('--port', type=str, default='/dev/rfcomm0', help="Serial port for MyoWare (e.g., COM5 or /dev/rfcomm0)")
    parser.add_argument('--baudrate', type=int, default=115200, help="Serial baud rate")
    parser.add_argument('--test', action='store_true', help="Disable inference and just print sensor values")

    return parser.parse_args()

def main():
    args = parse_args()

    client = PhosphoApi(base_url="http://localhost:80")
    allcameras = AllCameras()
    model = ACT()

    sensor_values = deque(maxlen=args.mean_window)

    try:
        # Connect to sensor serial
        with serial.Serial(args.port, args.baudrate, timeout=0) as bt_serial:
            print(f"Connected to {args.port} at {args.baudrate} baud.")
            time.sleep(2.0)  # Camera warmup

            while True: 
                latest_line = None
                while bt_serial.in_waiting: 
                    latest_line = bt_serial.readline().decode('utf-8', errors='replace').strip()
                
                if latest_line and latest_line.isdigit(): 
                    value = int(latest_line)
                    sensor_values.append(value)
                    filtered_val = np.mean(sensor_values) if args.mean else value
                    print(f"Sensor value: {filtered_val:.1f} | {args.threshold}")

                    # Check sensor value 
                    if filtered_val > args.threshold and not args.test:
                        # Get camera frames
                        images = [allcameras.get_rgb_frame(cam_id, resize=(320, 240)) for cam_id in args.camera_ids]
                        # Get robot state
                        state = client.control.read_joints()
                        # Run inference
                        actions = model({"state": np.array(state.angles_rad), "images": np.array(images)})

                        for action in actions:
                            client.control.write_joints(angles=action.tolist())
                            print("Action:", action)
                            time.sleep(1 / 30)

    except serial.SerialException as e:
        print(f"Failed to connect: {e}")
    except KeyboardInterrupt:
        print("Exiting gracefully.")

if __name__ == "__main__":
    main()
