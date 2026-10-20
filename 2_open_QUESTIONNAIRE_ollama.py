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
import sys
import re
import gc
import time
import json
import base64
import asyncio
import aiohttp
import requests
import subprocess
import cv2
import numpy as np
import sounddevice as sd
import openwakeword
from faster_whisper import WhisperModel

# Force immediate garbage collection and establish device audio properties
gc.collect()

# 1. Path-Resistant Robust Architecture Setup
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# Climbs out of script directory if nested, or anchors to root dynamically
WORKSPACE_ROOT = os.path.abspath(SCRIPT_DIR)

# Dynamically construct relative paths so it works out-of-the-box on any Raspberry Pi
SERVER_BINARY = os.path.join(WORKSPACE_ROOT, "llama.cpp", "build", "bin", "llama-server")
MODEL_PATH = os.path.join(WORKSPACE_ROOT, "smolvlm_models", "SmolVLM2-500M-Video-Instruct-Q8_0.gguf")
MMPROJ_PATH = os.path.join(WORKSPACE_ROOT, "smolvlm_models", "mmproj-SmolVLM2-500M-Video-Instruct-Q8_0.gguf")

PIPER_DIR = os.path.join(WORKSPACE_ROOT, 'INSERT_ALL_PIPER_FILES')
PIPER_BIN = os.path.join(PIPER_DIR, 'piper', 'piper')
PIPER_MODEL = os.path.join(PIPER_DIR, 'en_US-ljspeech-medium.onnx')
WAKEWORD_MODEL_PATH = os.path.join(WORKSPACE_ROOT, 'INSERT_ALL_HEY_BUDDY', 'hey-buddy.onnx')

# Handle eSpeak paths for ARM64 Linux cleanly
os.environ['ESPEAK_DATA_PATH'] = '/usr/lib/aarch64-linux-gnu/espeak-ng-data'

# 2. Audio Hardware Configuration & Auto-Detection
PORT = 8080
FORMAT = 'int16'
CHANNELS = 1
HARDWARE_RATE = 48000
TARGET_RATE = 16000
CHUNK = int(1280 * (HARDWARE_RATE / TARGET_RATE))

def get_input_device():
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if any(x in dev['name'].lower() for x in ['default', 'pulse', 'pipewire', 'istore']) and dev['max_input_channels'] > 0:
            return idx
    for idx, dev in enumerate(devices):
        if dev['max_input_channels'] > 0 and 'hdmi' not in dev['name'].lower():
            return idx
    raise RuntimeError("❌ No input device with recording channels found!")

TARGET_DEVICE_INDEX = get_input_device()
sd.default.device = [TARGET_DEVICE_INDEX, TARGET_DEVICE_INDEX]

# 3. Pre-Flight Asset Verification Check
missing_assets = []
if not os.path.exists(SERVER_BINARY): missing_assets.append(f"Llama Server Binary: {SERVER_BINARY}")
if not os.path.exists(MODEL_PATH): missing_assets.append(f"Model Weights: {MODEL_PATH}")
if not os.path.exists(MMPROJ_PATH): missing_assets.append(f"Projector Weights: {MMPROJ_PATH}")
if not os.path.exists(PIPER_BIN): missing_assets.append(f"Piper Binary: {PIPER_BIN}")
if not os.path.exists(PIPER_MODEL): missing_assets.append(f"Piper Model: {PIPER_MODEL}")
if not os.path.exists(WAKEWORD_MODEL_PATH): missing_assets.append(f"Wakeword File: {WAKEWORD_MODEL_PATH}")

if missing_assets:
    print("\n❌ Setup Architecture Error: Missing critical files or directory targets:")
    for asset in missing_assets:
        print(f" -> {asset}")
    print("\nPlease follow README instructions to place assets into this directory structure.\n")
    sys.exit(1)

print("⚡ Spawning global llama-server process optimized for low-latency...", flush=True)
global_server = subprocess.Popen([
    SERVER_BINARY, "-m", MODEL_PATH, "--mmproj", MMPROJ_PATH, "--port", str(PORT), "--host", "127.0.0.1",
    "-t", "4",          # Pinned execution directly to physical ARM64 CPU cores
    "-b", "256",        # Small batch constraints eliminate memory allocations lag
    "-c", "256"         # Tiny context envelope yields massive prompt-evaluation performance boosts
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

print("⏳ Warming up local vision model weights in RAM...", flush=True)
for _ in range(60):
    try:
        if requests.get(f"http://127.0.0.1:{PORT}/health", timeout=1).status_code == 200:
            print("🚀 Local VLM Engine active and listening!", flush=True)
            break
    except Exception:
        pass
    time.sleep(1)

# 4. Functional Audio & Output Routines
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

async def speak(text):
    if not text.strip():
        return
    print(f"Assistant: {text}")
    
    PIPER_RATE = 22050
    HARDWARE_RATE = 48000 
    
    try:
        piper_proc = await asyncio.create_subprocess_exec(
            PIPER_BIN, '-m', PIPER_MODEL, '--output_raw',
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
        )
        aplay_proc = await asyncio.create_subprocess_exec(
            'aplay', '-D', 'pulse', '-t', 'raw', '-r', str(HARDWARE_RATE), '-f', 'S16_LE', '-c', '2', '-q',
            stdin=asyncio.subprocess.PIPE
        )
        
        async def write_text():
            piper_proc.stdin.write(text.encode('utf-8'))
            await piper_proc.stdin.drain()
            piper_proc.stdin.close()

        write_task = asyncio.create_task(write_text())
        
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

        aplay_proc.stdin.close()
        await asyncio.gather(write_task, piper_proc.wait(), aplay_proc.wait())
        
    except Exception as e:
        print(f"Streaming TTS playback error: {e}")

# 5. Non-Blocking Llama Server VLM Core Stream Logic
async def llamacpp_tts_stream_async(user_prompt, base64_image):
    url = f"http://127.0.0.1:{PORT}/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    formatted_image_url = f"data:image/jpeg;base64,{base64_image}"
    
    payload = {
        "model": "local-model",
        "messages": [
            {
                "role": "system",
                "content":  "You are a helpful peer giving a general but precise description of the image and its content."
                            "Rules: Max length is two short simple sentences. No markdown, no asterisks, "
                            "no lists, no headers, no text emojis. Never say words like smiling face or smiley. "
                            "Be highly concise and never repeat yourself."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Question: {user_prompt}"},
                    {"type": "image_url", "image_url": {"url": formatted_image_url}}
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 64,  # Clamped to prevent VLM rambling latency
        "stream": True
    }
    
    temp_speech = ""
    punctuation_split_regex = re.compile(r'(?<=[.;:?\!—,])\s+|(?<=\.\.\.)\s+')
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    print(f"❌ Server Stream Error ({response.status})")
                    return

                async for line_bytes in response.content:
                    if not line_bytes:
                        continue
                    decoded_line = line_bytes.decode("utf-8").strip()
                    if decoded_line.startswith("data:"):
                        decoded_line = decoded_line[5:].strip()
                    if not decoded_line or decoded_line == "[DONE]":
                        continue
                    try:
                        chunk_data = json.loads(decoded_line)
                        if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            choice = chunk_data["choices"][0]
                            chunk = choice.get("delta", {}).get("content", "") or choice.get("text", "")
                            if chunk:
                                temp_speech += chunk
                                sentences = punctuation_split_regex.split(temp_speech)
                                if len(sentences) > 1:
                                    for complete_sentence in sentences[:-1]:
                                        if complete_sentence.strip():
                                            await speak(complete_sentence.strip())
                                    temp_speech = sentences[-1]
                    except Exception:
                        pass
        except Exception as e:
            print(f"Stream exception: {e}")
            
    if temp_speech.strip():
        await speak(temp_speech.strip())

# 6. Primary Unified Execution Core
async def main():
    cam_url = "http://192.168.4.1/Test"
    
    print("⏳ Loading wake word engine and Whisper weights into system RAM...")
    ww_model = openwakeword.model.Model(wakeword_models=[WAKEWORD_MODEL_PATH], inference_framework='onnx')

    try:
        whisper_model = WhisperModel("base", device="cpu", compute_type="int8", local_files_only=True)
        print("✓ Whisper loaded successfully from local offline cache.")
    except Exception:
        print("🌐 Offline Whisper cache empty. Downloading base model files from upstream servers...")
        whisper_model = WhisperModel("base", device="cpu", compute_type="int8", local_files_only=False)
    
    mic_stream = sd.RawInputStream(
        samplerate=HARDWARE_RATE, blocksize=CHUNK, dtype=FORMAT, channels=CHANNELS, device=TARGET_DEVICE_INDEX
    )
    
    await speak("System online and ready.")
    
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
                
                prediction = ww_model.predict(audio_frame_resampled)
                score = list(prediction.values())[0]
                
                if score > 0.45:
                    print(f"✨ Wake word detected! (Score: {score:.2f})")
                    play_native_chime()
                    
                    # Track query data matrix window
                    live_buffer = []
                    for _ in range(47):  # ~3 seconds recording window
                        chunk_data_whisperer, overflow = mic_stream.read(CHUNK)
                        live_buffer.append(chunk_data_whisperer)
                    
                    # Process Video Frame capture with network queue mitigation
                    base64_image = None
                    cam = cv2.VideoCapture(cam_url)
                    if cam.isOpened():
                        for _ in range(5):  # Empty frame queue cache to clear visual delay
                            cam.grab()
                        ret, frame = cam.read()
                        cam.release()
                        
                        if ret:
                            frame = cv2.resize(frame, (384, 384))
                            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                            base64_image = base64.b64encode(buffer.tobytes()).decode('utf-8')
                    
                    if not base64_image:
                        print("Image Capture Error")
                        await speak("Image Capture Error")
                        continue
                    
                    # Convert raw linear audio arrays for Whisper evaluation
                    unified_bytes = b"".join(live_buffer)
                    whisper_input = np.frombuffer(unified_bytes, dtype=np.int16).astype(np.float32).flatten()
                    
                    whisper_target_samples = int(len(whisper_input) * TARGET_RATE / HARDWARE_RATE)
                    whisper_input_resampled = np.interp(
                        np.linspace(0, len(whisper_input) - 1, whisper_target_samples),
                        np.arange(len(whisper_input)),
                        whisper_input
                    ) / 32768.0
                    
                    print("Processing speech with Whisper...")
                    segments, info = whisper_model.transcribe(whisper_input_resampled, beam_size=3, language="en")
                    transcribed_text = "".join([segment.text for segment in segments]).strip()
                    print(f"User said: {transcribed_text}")
                    
                    if transcribed_text:
                        await llamacpp_tts_stream_async(transcribed_text, base64_image)
                    else:
                        print("⚠️ Skipping VLM: Empty translation transcription sequence string.")
                    
                    ww_model.reset()
                    
                    # Flush the remaining frame loop registers
                    try:
                        while mic_stream.read(mic_stream.get_read_available()):
                            pass
                    except Exception:
                        pass
                
                # Relinquish processing cycle slices to keep background routines clear
                await asyncio.sleep(0.001)
                
    except KeyboardInterrupt:
        print("\nStopping audio stream...")
    finally:
        print("\n🧼 Script terminating. Force closing server process and purging allocations...", flush=True)
        global_server.terminate()
        global_server.wait()
        print("🔒 System memory cleared completely. Goodbye!", flush=True)

if __name__ == "__main__":
    asyncio.run(main())