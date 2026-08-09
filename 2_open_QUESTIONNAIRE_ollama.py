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
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
os.environ['ESPEAK_DATA_PATH'] = '/usr/lib/aarch64-linux-gnu/espeak-ng-data'
gc.collect()
def get_input_device():
    devices = sd.query_devices()
    for idx, dev in enumerate(devices):
        if dev['name'] in ['default', 'pulse'] and dev['max_input_channels'] > 0:
            return idx
    for idx, dev in enumerate(devices):
        if dev['max_input_channels'] > 0:
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

def speak(text):
    print(f"Assistant: {text}")
    #DOWNLOAD PIPER AND ITS FILES VIA README INSTRUCTIONS
    piper_path = os.path.join(SCRIPT_DIR, 'INSERT_ALL_PIPER_FILES', 'piper_src', 'build', 'piper')
    model_path = os.path.join(SCRIPT_DIR, 'INSERT_ALL_PIPER_FILES', 'en_US-ljspeech-medium.onnx')

    try:
        piper_proc = subprocess.Popen(
            [piper_path, '-m', model_path, '--output_raw'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        piper_proc.stdin.write(text.encode('utf-8'))
        piper_proc.stdin.flush()
        piper_proc.stdin.close()
        
        raw_audio = piper_proc.stdout.read()
        piper_proc.wait()
        
        if raw_audio:
            mono_array = np.frombuffer(raw_audio, dtype=np.int16)
            piper_rate = 22050
            num_output_samples = int(len(mono_array) * HARDWARE_RATE / piper_rate)
            resampled_mono = np.interp(
                np.linspace(0, len(mono_array) - 1, num_output_samples),
                np.arange(len(mono_array)),
                mono_array
            ).astype(np.int16)
            
            stereo_samples = np.repeat(resampled_mono, 2).tobytes()
            
            aplay_proc = subprocess.Popen(
                ['aplay', '-D', 'pulse', '-t', 'raw', '-r', '48000', '-f', 'S16_LE', '-c', '2', '-q'],
                stdin=subprocess.PIPE
            )
            aplay_proc.stdin.write(stereo_samples)
            aplay_proc.stdin.flush()
            aplay_proc.stdin.close()
            aplay_proc.wait()
    except Exception as e:
        print(f"Streaming TTS playback error: {e}")

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

speak("System online and ready.")

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
            
            if score > 0.4:
                print("✨ Wake word detected! (Score: {:.2f})".format(score))
                play_native_chime()
                
                live_buffer = []
                for _ in range(63):
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
                    speak("Image Capture Error")
                
                unified_bytes = b"".join(live_buffer)
                whisper_input = np.frombuffer(unified_bytes, dtype=np.int16).astype(np.float32).flatten()
                
                whisper_target_samples = int(len(whisper_input) * TARGET_RATE / HARDWARE_RATE)
                whisper_input_resampled = np.interp(
                    np.linspace(0, len(whisper_input) - 1, whisper_target_samples),
                    np.arange(len(whisper_input)),
                    whisper_input
                )
                
                whisper_input_final = (whisper_input_resampled / 32768.0)
                
                print("🦻 Processing speech with Whisper...")
                
                segments, info = whisper_model.transcribe(whisper_input_final, beam_size=5)
                transcribed_text = "".join([segment.text for segment in segments]).strip()
                
                print(f"User said: {transcribed_text}")
                
                ollama_result = ollama.chat(
                    model='ahmadwaqar/smolvlm2-2.2b-instruct',
                    keep_alive=-1,
                    messages=[
{
    'role': 'user',
    'content': f"""User's Question: "{transcribed_text}"

Instruction: Look at the image and answer the user's question with absolute factual accuracy. Do not guess, do not assume, and do not hallucinate obstacles or safety status. You may describe human emotions if relevant to the question, but absolutely never use text words to describe emojis or facial expressions (like "smiling face", "wink", or "smiley").

Reply using these strict rules:
1. Max length: Two short, simple sentences.
2. Tone: Speak completely naturally like a helpful peer.
3. Formatting: Absolutely NO markdown, lists, asterisks, headers, or text emojis.""",
    'images': image_payload
}
                    ],
                    options={'num_thread': 4}
                )
                
                print(ollama_result['message']['content'])
                speak(ollama_result['message']['content'])
                
                model.reset()
                
                try:
                    while mic_stream.read(mic_stream.get_read_available()):
                        pass
                except Exception:
                    pass
                continue

except KeyboardInterrupt:
    print("\nStopping audio stream...")
