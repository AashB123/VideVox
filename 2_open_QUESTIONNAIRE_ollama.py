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

import numpy as np 
import sounddevice as sd 
import soundfile as sf 
import openwakeword 
import subprocess 
import os 
import cv2
import ollama
import time
import base64
import gc
from faster_whisper import WhisperModel
import asyncio

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
os.environ['ESPEAK_DATA_PATH'] = '/usr/lib/aarch64-linux-gnu/espeak-ng-data'

gc.collect()

def get_input_device():
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if any(x in dev['name'].lower() for x in ['default', 'pulse', 'pipewire', 'istore']) and dev['max_input_channels'] > 0:
            return idx
    for idx, dev in enumerate(devices):
        if dev['max_input_channels'] > 0 and 'hdmi' not in dev['name'].lower():
            return idx
    raise RuntimeError("No input device with recording channels found!")

TARGET_DEVICE_INDEX = get_input_device()

sd.default.device = [TARGET_DEVICE_INDEX, TARGET_DEVICE_INDEX]

FORMAT = 'int16'
CHANNELS = 1
HARDWARE_RATE = 48000
TARGET_RATE = 16000
CHUNK = int(1280 * (HARDWARE_RATE / TARGET_RATE))

def play_native_chime():
    sample_rate = 48000
    duration = 0.15
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = np.sin(2 * np.pi * 880 * t)
    fade_out = np.linspace(1.0, 0.0, len(t))
    mono_samples = (tone * fade_out * 32767).astype(np.int16)
    stereo_samples = np.repeat(mono_samples, 2).tobytes()
    try:
        aplay_process = subprocess.Popen(
            ['aplay', '-D', 'pulse', '-t', 'raw', '-r', '48000', '-f', 'S16_LE', '-c', '2', '-q'],
            stdin=subprocess.PIPE
        )
        aplay_process.stdin.write(stereo_samples)
        aplay_process.stdin.flush()
        aplay_process.stdin.close()
        aplay_process.wait()
    except Exception as e:
        print(f"System chime error: {e}")

async def speak(text): #Piper speaking stream
    print(f"Assistant: {text}")
    piper_path = '/home/bumba/visual_assistant/piper_src/build/piper'
    model_path = '/home/bumba/visual_assistant/models/tts/en_US-ljspeech-medium.onnx'
    
    PIPER_RATE = 22050
    HARDWARE_RATE = 48000 
    
    try:
        # Start processes
        piper_proc = await asyncio.create_subprocess_exec(
            piper_path, '-m', model_path, '--output_raw',
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL
        )
        
        aplay_proc = await asyncio.create_subprocess_exec(
            'aplay', '-D', 'pulse', '-t', 'raw', '-r', str(HARDWARE_RATE), '-f', 'S16_LE', '-c', '2', '-q',
            stdin=asyncio.subprocess.PIPE
        )
        
        # Helper coroutine to write text safely without blocking the read loop
        async def write_text():
            piper_proc.stdin.write(text.encode('utf-8'))
            await piper_proc.stdin.drain()
            piper_proc.stdin.close()

        # Start writing text in the background
        write_task = asyncio.create_task(write_text())
        
        # Read chunk-by-chunk from Piper, resample, and stream straight to Aplay
        while True:
            chunk = await piper_proc.stdout.read(4096)
            if not chunk:
                break 
                
            mono_array = np.frombuffer(chunk, dtype=np.int16)
            if len(mono_array) == 0:
                continue
                
            num_output_samples = int(len(mono_array) * HARDWARE_RATE / PIPER_RATE)
            resampled_mono = np.interp(
                np.linspace(0, len(mono_array) - 1, num_output_samples),
                np.arange(len(mono_array)),
                mono_array
            ).astype(np.int16)
            
            stereo_samples = np.repeat(resampled_mono, 2).tobytes()
            
            aplay_proc.stdin.write(stereo_samples)
            await aplay_proc.stdin.drain()

        # Clean up
        aplay_proc.stdin.close()
        await asyncio.gather(write_task, piper_proc.wait(), aplay_proc.wait())
        
    except Exception as e:
        print(f"Streaming TTS playback error: {e}")

ollama_model_names = [model.model for model in ollama.list().models]

try:
    if "hf.co/ggml-org/SmolVLM2-500M-Video-Instruct-GGUF:Q8_0" in ollama_model_names:
        print("VLM Model Found")

    else:
        print("VLM Model NOT Found")
        print("Initializing Download for the VLM")
        ollama.pull("hf.co/ggml-org/SmolVLM2-500M-Video-Instruct-GGUF:Q8_0")
except:
    print("VLM Extraction Error Occurred")

async def ollama_tts_stream(user_prompt): #VLM audio stream
    ollama_result = ollama.chat(
        model='hf.co/ggml-org/SmolVLM2-500M-Video-Instruct-GGUF:Q8_0',
        keep_alive=-1,
        messages=[
            # 1. Isolate the formatting rules completely into the system role
            {
                'role': 'system',
                'content': (
                    "You are a helpful peer giving a general but precise description of the image and its content."
                    "Rules: Max length is two short simple sentences. No markdown, no asterisks, "
                    "no lists, no headers, no text emojis. Never say words like smiling face or smiley. "
                    "Be highly concise and never repeat yourself."
                )
            },
            # 2. Keep the user role incredibly clean and focused purely on the question and image
            {
                'role': 'user',
                'content': f"Question: {user_prompt}",
                'images': image_payload
            }
        ],
        options={
            'num_thread': 4,
            "num_ctx": 1024,
            "temperature": 0.1,  # Keep this low so it stays predictable
        },
        stream=True
    )
    punctuation_pauses = (";", ":", "...", "—", ".", "?", "!")
    temp_speech=""
    for chunk in ollama_result:
        chunk_sent = chunk.message.content
        temp_speech += chunk_sent

        if chunk_sent and chunk_sent[-1] in punctuation_pauses:
            await speak(temp_speech)
            temp_speech = ""

    if temp_speech.strip():
        await speak(temp_speech)

#Initializing models and mics

url="http://192.168.4.1/Test"
#DOWNLOAD HEY_BUDDY FILE VIA README INSTRUCTIONS
WW_PATH = os.path.join(SCRIPT_DIR, 'INSERT_ALL_HEY_BUDDY', 'hey-buddy.onnx')
model = openwakeword.model.Model(wakeword_models=[WW_PATH], inference_framework='onnx')

try:
    whisper_model = WhisperModel(
        "base", 
        device="cpu", 
        compute_type="int8", 
        local_files_only=True
    )
    print("Whisper loaded successfully from local cache (Offline Mode).")
except Exception:
    print("Model not found locally. Connecting to internet to download...")
    whisper_model = WhisperModel(
        "base", 
        device="cpu", 
        compute_type="int8", 
        local_files_only=False
    )
    print("Whisper downloaded and loaded successfully.")


mic_stream = sd.RawInputStream(
    samplerate=HARDWARE_RATE,
    blocksize=CHUNK,
    dtype=FORMAT,
    channels=CHANNELS,
    device=TARGET_DEVICE_INDEX
)

asyncio.run(speak("System online and ready."))

try:
    with mic_stream:
        while True:
            raw_data, overflow = mic_stream.read(CHUNK)
            audio_frame = np.frombuffer(raw_data, dtype=np.int16)
            num_target_samples = int(len(audio_frame) * TARGET_RATE / HARDWARE_RATE)
            audio_frame_resampled = np.interp(
                np.linspace(0, len(audio_frame) - 1, num_target_samples),
                np.arange(len(audio_frame)),
                audio_frame
            ).astype(np.int16)
            
            prediction = model.predict(audio_frame_resampled)
            score = list(prediction.values())[0]
            
            if score > 0.45:
                print("✨ Wake word detected! (Score: {:.2f})".format(score))
                play_native_chime()
                
                live_buffer = []
                for _ in range(47):
                    chunk_data_whisperer, overflow = mic_stream.read(CHUNK)
                    live_buffer.append(chunk_data_whisperer)
                
                image_payload = []
                cam = cv2.VideoCapture(url)
                ret, frame = cam.read()
                cam.release()
                
                if ret:
                    frame = cv2.resize(frame, (384, 384))
                    _, buffer = cv2.imencode('.jpg', frame)
                    base64_image = base64.b64encode(buffer.tobytes()).decode('utf-8')
                    image_payload = [base64_image]
                else:
                    print("Image Capture Error")
                    asyncio.run(speak("Image Capture Error"))
                
                unified_bytes = b"".join(live_buffer)
                whisper_input = np.frombuffer(unified_bytes, dtype=np.int16).astype(np.float32).flatten()
                
                whisper_target_samples = int(len(whisper_input) * TARGET_RATE / HARDWARE_RATE)
                whisper_input_resampled = np.interp(
                    np.linspace(0, len(whisper_input) - 1, whisper_target_samples),
                    np.arange(len(whisper_input)),
                    whisper_input
                )
                
                whisper_input_final = (whisper_input_resampled / 32768.0)
                
                print("Processing speech with Whisper...")
                
                segments, info = whisper_model.transcribe(whisper_input_final, beam_size=5, language="en")
                transcribed_text = "".join([segment.text for segment in segments]).strip()
                
                print(f"User said: {transcribed_text}")
                
                asyncio.run(ollama_tts_stream(transcribed_text))
                
                model.reset()
                
                try:
                    while mic_stream.read(mic_stream.get_read_available()):
                        pass
                except Exception:
                    pass
                continue

except KeyboardInterrupt:
    print("\nStopping audio stream...")
