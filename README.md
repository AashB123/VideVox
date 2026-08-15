# VideVox

VideVox is an offline, edge-based visual assistant designed for the Raspberry Pi 5 to help visually impaired individuals achieve greater independence and self-reliance. By decoupling high-frequency spatial tracking from conversational image analysis, the system provides real-time obstacle detection alongside an interactive audio question-answering mode.

The entire system runs locally to ensure absolute data privacy, delivering audio feedback directly to the user's earbuds via a simple, physical two-button control interface.

---

## System Requirements

Before running the scripts, ensure your hardware and software environment meet the following specifications.

### 1. Hardware Specifications
* Processing Unit: Raspberry Pi 5 (8GB RAM highly recommended)
* Camera Module: ESP32 Camera Module ([Elegoo Smart Camera](https://www.amazon.com/Arduino-Robotics-Science-Engineering-Building/dp/B07KPZ8RSZ?crid=30WB9PQD7IBBJ&dib=eyJ2IjoiMSJ9.babjSmpE-3D55bL50SAvWcCJD4jgj_qT3WrIcclw86xRlTL2r7GImmORo63epZ0K_e9xFfHI32O0DFQQVJcfsTJQ3N2zWpPkb7gyMZpVSoRMaytse6KeyS61AW1PTU2PSWX7yr79YzLydo1GOchyHfOe_5EzTsAkCf3Fy3fh3D8KjePTCavJrGrXqgTxyi9OwkXS0CYyZf2BUkr75_2usZWg7NGu5CH7o1P5MRUlQ1NhdAA2mV4F9a7gSrfU1zkpAqzQWX2-yeWO1pDwAz_yDjqM17b0h4K10OyDG0qIgwg.8dfbuhJv9khZZJXSrW04ptH9GAhqxoMhKQLioKXOX5k&dib_tag=se&keywords=elegoo+robot&qid=1786749361&sprefix=elegoo+robot%2Caps%2C222&sr=8-3) recommended)
* Audio Interface: USB-to-TRRS Audio Adapter ([STSAUX Adapter](https://www.amazon.com/Adapter-External-Converter%EF%BC%8CSTSAUX-Windows-Desktops/dp/B0FJ74YMYY?crid=W9VPXPQKUG1V&dib=eyJ2IjoiMSJ9.iTbfh8RW9olQ0LnCNCoH27LtBttg1Fd2UgZ3pJsN2XXJFfNih3j7uA13MjrYb3dAwbBwCtrcMSvsSDhl1Br733lwUMM35djhYd1MVpY_hH90nowfs2qL3CBsn0jWVTZ89KSZUg6FTXW8lEG4LmaT2rCNtG25kEDIxKsVOMAGHk17GFjbzQwwvVX5RlT8h-dC1yovGaym-a4m4Fow3HErjnOpU3KvUYalsZD0L4o1Hkk.ABTgeX_vmQyYPQCfa_QtyQXAB5CasT54BUHxBoFcmks&dib_tag=se&keywords=trrs+usb+adapter&qid=1786749260&refinements=p_36%3A-600&rnid=386442011&sprefix=trrs+usb+adapt%2Caps%2C189&sr=8-3) recommended)
* Audio Output: TRRS Earbuds with Microphone ([Onn Wired Earphones](https://www.walmart.com/ip/onn-Wired-Earphones-with-Mic-3-5mm-jack-Black/416099849?classType=VARIANT&athbdg=L1102&from=/search) recommended)
* Cabling: USB-to-USB Type-C cable for the camera module
* Tactile Inputs: 2x GPIO momentary buttons ([MakerSpot Buttons](https://www.amazon.com/MakerSpot-Momentary-Extension-Breadboard-Friendly/dp/B01J9KO7DC?crid=181HI5D5KHB67&dib=eyJ2IjoiMSJ9.IIRtTWquS4k2qoxkU791h6rrm0gRAsaCQDD5c9Oe4ezbIeY2NoJfmn5vQik5rw-qGxWSbhPR6sghPTf3pcQe8J-8cakRUj5JFCUuGsc-raI5Y_yT49kmybePA5bVrAE4MAx4cwQenJ6eGwSxwRaC75p6_3BzemDYCPFTUDaq5wYiP15iNdE_6Bk-7zArtQS0DUWZFODwq04oQ67ErwFteSf1h5J0aCOUZDxDTI8pq4w.PYUwkakAgLTvL1BxSKgsKj4DbrSb4r_GwSNlrNZX_JE&dib_tag=se&keywords=5+pack+buttons+for+rpi+dupont&qid=1786749780&sprefix=5+pack+buttons+for+rpi+dupont%2Caps%2C166&sr=8-10) recommended)
  * Detection Button: Connected to GPIO 16
  * Questionnaire Button: Connected to GPIO 18

### 2. Operating System & Environment
* OS: Linux Debian-based 64-bit ARM (Raspberry Pi OS 64-bit)
* Environment: Local execution environment with full terminal command privileges

### 3. Programming Language
* Python: Version 3.12 is required for optimal package execution (3.12.13 recommended)

---

## Installation Blueprint

Follow these step-by-step terminal commands to extract the application, isolate dependencies inside a dedicated Python 3.12 virtual environment, and fetch required asset files.

### 1. Extract and Navigate to the Project Folder
Assuming the project source ZIP archive was downloaded to your default directory, execute the following commands to extract and enter the repository:

```bash
cd ~/Downloads
unzip *.zip
cd visual_assistant
```
> Note: Ensure your terminal or source code editor is working inside the `visual_assistant` project root directory so that internal file paths resolve properly.

### 2. Set Up a Python 3.12 Virtual Environment
Isolate your project dependencies from global system packages to prevent library version conflicts:

```bash
# Initialize the virtual environment using Python 3.12
python3.12 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```
*(Your terminal prompt will now display `(venv)` at the beginning of the line, confirming activation).*

### 3. Install System-Level Dependencies & Python Packages
Install the required backend audio drivers, compilation libraries, and Python dependencies:

```bash
# Update local package manager and install system utilities
sudo apt update
sudo apt install -y espeak portaudio19-dev

# Upgrade package installer and fetch python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Fetch Asset & Model Files Manually
To ensure full offline capabilities, manually download and place the following files into their respective folders:

* Piper TTS Binary: Download the Linux AArch64 archive from [Rhasspy Piper Releases](https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_aarch64.tar.gz). Extract it and move its entire contents into the `INSERT_ALL_PIPER_FILES/` directory.
* Piper Voice Model: Download `en_US-ljspeech-medium.onnx` and `en_US-ljspeech-medium.onnx.json` from the [Hugging Face Piper Voices Repository](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/ljspeech/medium). Place both files inside the `INSERT_ALL_PIPER_FILES/` directory.
* Wake Word Model: Download `hey-buddy.onnx` from [Benjamin Paine's Hugging Face Space](https://huggingface.co/benjamin-paine/hey-buddy/resolve/main/models/hey-buddy.onnx?download=true). Place it directly into the `INSERT_ALL_HEY_BUDDY/` directory.

---

## Execution & Usage Guide

Ensure your virtual environment is active before starting any core script execution.

```bash
source venv/bin/activate
```

### 1. Launching Application Modes
Run the specific script from the repository root depending on your immediate operational requirement:

* Production Mode (Combined): Launches both the VLM capabilities and physical button-triggered tracking interfaces.
  ```bash
  python OPEN_SOURCING_CODE/0_open_button.py
  ```
* Object Detection Only Mode: Focuses purely on low-latency tracking and spatial layout updates.
  ```bash
  python OPEN_SOURCING_CODE/1_open_YOLO_detection.py
  ```
* Questionnaire Only Mode: Launches the offline local vision-language model loop running via Ollama.
  ```bash
  python OPEN_SOURCING_CODE/2_open_QUESTIONNAIRE_ollama.py
  ```

### 2. Safety & System Termination
If you need to instantly halt running tasks or safely clear hung text-to-speech audio frames from system memory, open a parallel terminal tab and run:

```bash
pkill -f python
pkill -f espeak
```

---

## Technical Architecture & How It Works

VideVox features a decoupled edge architecture that protects processing bandwidth by running tracking routines at a light, steady frame rate while isolating intensive VLM tasks to an on-demand thread.

### 1. High-Frequency Tracking Pipeline (`1_open_YOLO_detection.py`)
This script loops continuously to identify immediate obstacles and track clear paths.

* Frame Optimization: The system dynamically determines the video dimensions using frame_w and frame_h, falling back to a standard 800x600 resolution if the camera properties cannot be read. To optimize thermals and prevent CPU throttling, model inference runs exclusively on **every second frame**.
* ONNX Inference: Standard PyTorch models drop tracking speeds to an unusable 1–6 FPS. VideVox uses an optimized, raw **YOLO26n.onnx** runtime running straightforward prediction logic (`model.predict()`) to secure a smooth **19 FPS**.
* Spatial Partitioning: The frame grid is split horizontally into three equal sections. The system evaluates the absolute center point of an object's bounding box to announce its location as **Left**, **Center**, or **Right**.
* Depth Calculation: Proximity is mapped by calculating the screen occupancy percentage:

  
  $$\text{Proximity \%} = \frac{\text{Width} \times \text{Height}}{\text{frame}_w \times \text{frame}_h}$$

  
  Detected items are sorted sequentially in an array from closest to farthest.
* Priority Threat Management:
  * High Danger (≥ 32% view): Instantly forces smaller speech tasks to close using `pkill -f espeak` to play a critical, real-time warning.
  * Lower Danger (15% to 32%): Announces the object's relative direction and applies a strict 5-second cooldown timer to prevent speech overstimulation.
  * No Danger (< 15%): Muted entirely to maintain a clean audio environment.

### 2. Conversational VLM Questionnaire Pipeline (`2_open_QUESTIONNAIRE_ollama.py`)
This pipeline triggers a highly responsive local voice-to-vision loop whenever detailed environmental context is requested.

* Audio Hardware Alignment: Standard voice transcription modules crash on the Pi because they expect 16,000 Hz audio streams. VideVox sets up a direct, custom hardware channel to safely capture raw audio from the hardware adapter running at **48,000 Hz**.
* Wake Word Verification: A background thread reads audio frames via an OpenWakeWord wrapper. It utilizes a **Hey-Buddy ONNX model** tuned to a conservative 40% confidence threshold to guarantee immediate responsiveness.
* Context Capture & Transcription: Once triggered, a 3-second mic buffer is passed directly to a local **`faster-whisper`** engine. This extracts clean text tokens while avoiding the memory leaks found in default language bindings.
* Local Vision-Language Model: Text queries and raw image bytes are bundled and routed to a quantized **SmolVLM2-500M-Video-Instruct-GGUF (Q8_0)** model running locally via Ollama. 
* Latency Optimizations: Turnaround latency was successfully minimized from 30 seconds down to **11 seconds** total by hardcoding strict backend engine options:
  ```python
  options = {
      'num_thread': 4,       # Lock processing to the four physical CPU cores
      'num_ctx': 1024,       # Bound context window size to prevent memory bloat
      'temperature': 0.1,    # Enforce objective, literal physical scene analysis
      'num_predict': 15      # Cap response output length to maintain high speeds
  }
  ```
* Speech Synthesis: Output tokens pass straight into a native, high-speed, C-based **Piper TTS engine** utilizing an `LJSpeech-Medium` voice profile. This provides instant audio playback through user headphones, completely skipping heavy, Python-wrapped alternative setups.

---
## AI Usage & Project Disclosure

* **Core Foundation**: I designed, architected, and coded this entire application's base.
* **AI Assistance**: I utilized AI tools for localized project optimization, code debugging, and formatting.
* **Technical Ownership**: All system pipelines, conditional logic, and data parameters reflect my personal engineering work.

## License

This project is open-source and structured to maintain strict upstream compliance with its dependencies:
* Source Code: Distributed under the **Apache License 2.0**. For a link to the complete license terms, please see the accompanying [LICENSE](LICENSE) file.

---

## Credits & Acknowledgments

VideVox relies heavily on the amazing work published by the open-source software and machine learning engineering communities. While machine-readable dependency attributes can be viewed in our third-party-licenses.json file, we want to highlight the core architectures that made this single-board assistant possible:

* Ultralytics: For the underlying high-speed object checking structures that enabled smooth migration to an optimized YOLO26n platform.
* Hugging Face & Benjamin Paine: For hosting the foundational Hey-Buddy ONNX wake word model, providing a clean, production-ready audio gate.
* openWakeWord: For providing the lightweight, always-listening framework used for local background wake-word detection.
* Ollama & the GGML Team: For developing the low-footprint, local inference runtime that allows accurate SmolVLM2 layers to run entirely offline on localized edge hardware.
* Systran (faster-whisper): For engineering a streamlined, fast Speech-to-Text layer that avoids C-wrapper parsing bugs.
* **Rhasspy (Piper TTS)**: Creates high-performance, native speech synthesis binaries alongside clear, natural-sounding voice profiles.
  * `en_US-ljspeech-medium.onnx`: The trained C-based machine learning model binary handling low-latency voice inference.
  * `en_US-ljspeech-medium.onnx.json`: The phoneme and synthesis configuration map essential for accurate speech pronunciation and pacing based on the LJSpeech dataset.
* The Raspberry Pi Foundation: For delivering accessible, low-power single-board computer processing frameworks optimized for intense local AI development.
