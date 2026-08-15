# Copyright 2026 Aashuman Bandyopadhayay
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://apache.org
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import cv2
from ultralytics import YOLO
import subprocess
import torch
import gc
from pathlib import Path
import time

gc.collect()
torch.set_num_threads(2) 
torch.cuda.empty_cache()

os.chdir(os.path.dirname(os.path.abspath(__file__)))
if Path("yolo26n.onnx").is_file():
    print("YOLO FOUND")
    YOLOPATH = Path('yolo26n.onnx')
else:
    print("YOLO NOT FOUND")
    print("Downloading YOLO26N")
    download_pt = YOLO("yolo26n.pt")
    download_pt.export(format="onnx")
    os.remove("yolo26n.pt")
    YOLOPATH = Path('yolo26n.onnx')
model = YOLO(YOLOPATH)

# ENSURE THAT YOU ARE WIFI-CONNECTED TO THE CAMERA
url = "http://192.168.4.1/Test"

cap = cv2.VideoCapture(url)
already_warned_of_danger = False
audio_process = None
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
last_spoken_time = 0
class_names = model.names
frame_count = 0
skip_frame = 2

frame_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 800
frame_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 600
LEFT_BOUND = frame_w / 3
RIGHT_BOUND = (frame_w / 3) * 2

while True:
    for _ in range(5): 
        cap.grab()

    ret, frame = cap.read()
    if not ret:
        break
    frame_count += 1
    
    if frame_count % skip_frame == 0:
        locator_list = []
        frame_has_danger = False  # FIX: Track threat at frame scope to avoid NameError crash

        results_gen = model.predict(source=frame, conf=0.6, imgsz=640, show=False, verbose=False)
        results_single = results_gen if isinstance(results_gen, list) else results_gen

        if results_single.boxes is not None:
            class_ids = results_single.boxes.cls.int().cpu().tolist()
            boxes_xywh = results_single.boxes.xywh.cpu().numpy()

            for class_id, box in zip(class_ids, boxes_xywh):
                x_center, y_center, width, height = box
                names = class_names[class_id]
                area_percentage = (width * height) / (frame_w * frame_h)

                if area_percentage >= .15:
                    obj_danger = False
                    if area_percentage >= .32:
                        obj_danger = True
                        frame_has_danger = True  # FIX: Persistent flag preserves safety warnings

                    if x_center < LEFT_BOUND:
                        position = "on your left"
                    elif x_center > RIGHT_BOUND:
                        position = "on your right"
                    else:
                        position = "straight ahead"

                    locator_list.append({
                        "name": names,
                        "position": position,
                        "area": area_percentage,
                        "danger": obj_danger
                    })

        locator_list.sort(key=lambda x: x["area"], reverse=True)
        tts_saying = []

        for obj in locator_list:
            tts_obj = f"A {obj['name']} is {obj['position']} covering {round(obj['area'] * 100)}%"
            tts_saying.append(tts_obj)

        if tts_saying:
            current_time = time.time()
            current_cooldown = 0.5 if frame_has_danger else 5.0

            if current_time - last_spoken_time > current_cooldown:
                if frame_has_danger and not already_warned_of_danger:
                    if audio_process is not None and audio_process.poll() is None:
                        subprocess.run(["pkill", "-f", "espeak"], stderr=subprocess.DEVNULL)
                    already_warned_of_danger = True

                if not frame_has_danger:
                    already_warned_of_danger = False

                if audio_process is None or audio_process.poll() is not None:
                    tts = " , and ".join(tts_saying)
                    
                    if frame_has_danger:
                        tts = "STOP! " + tts

                    print(tts)
                    # FIX: Simplified directly to use your imported standard subprocess module
                    audio_process = subprocess.Popen(f'espeak -s 150 "{tts}"', shell=True)
                    last_spoken_time = current_time

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
