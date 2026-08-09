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

from gpiozero import Button
from signal import pause
import sys
import subprocess
import time
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
VENV_PYTHON = sys.executable
ESPEAK_BIN = "/usr/bin/espeak"

button_VLM = Button(18) #Connect a button to GPIO 18
button_YOLO = Button(16) #Connect another button to GPIO 16

# Track the actual running process objects
vlm_process = None
yolo_process = None

def speak_blocking(text):
    """Cuts off any existing voice and speaks a new padded sentence."""
    # 1. Forcefully kill any espeak process currently talking
    subprocess.run(['pkill', '-f', 'espeak'], stderr=subprocess.DEVNULL)
    
    # 2. Give the audio hardware a microscopic moment to clear
    time.sleep(0.1)
    
    # 3. Add the silent pad to wake up the hardware smoothly
    padded_text = " . . . " + text
    subprocess.run([ESPEAK_BIN, padded_text])

def kill_process(proc, name, speak_msg):
    """Safely kills a process if it is running."""
    if proc is not None and proc.poll() is None:
        print(f"Terminating {name}...")
        proc.terminate() # Clean shutdown request
        proc.wait()      # Ensure it is dead before moving on
        speak_blocking(speak_msg)
    return None

def VLM_clicked():
    global vlm_process, yolo_process
    try:
        # If VLM is running, turn it off
        if vlm_process is not None and vlm_process.poll() is None:
            vlm_process = kill_process(vlm_process, "Questionnaire Model", "Terminated Questionnaire Model")
        else:
            # If YOLO is running, turn it off first
            if yolo_process is not None and yolo_process.poll() is None:
                yolo_process = kill_process(yolo_process, "YOLO Model", "Terminated Detection Model")
            
            print("Running Questionnaire Model")
            speak_blocking("Running Questionnaire Model")
            vlm_process = subprocess.Popen([VENV_PYTHON, "2_open_QUESTIONNAIRE_ollama.py"])
    except Exception as e:
        print(f"Error VLM Button: {e}")

def YOLO_clicked():
    global vlm_process, yolo_process
    try:
        # If YOLO is running, turn it off
        if yolo_process is not None and yolo_process.poll() is None:
            yolo_process = kill_process(yolo_process, "YOLO Model", "Terminated Detection Model")
        else:
            # If VLM is running, turn it off first
            if vlm_process is not None and vlm_process.poll() is None:
                vlm_process = kill_process(vlm_process, "Questionnaire Model", "Terminated Questionnaire Model")
            
            print("Running Detection Model")
            speak_blocking("Running Detection Model")
            yolo_process = subprocess.Popen([VENV_PYTHON, r'1_open_YOLO_detection.py'])
    except Exception as e:
        print(f"Error YOLO Button: {e}")

button_VLM.when_pressed = VLM_clicked
button_YOLO.when_pressed = YOLO_clicked
pause()
