## Troubleshooting and Hardware Setup

If you encounter connection drops, dependency errors, or network timeout issues, follow this step-by-step verification pipeline to reset the runtime environment.

### Software Dependencies Issue

Ensure all dependencies are downloaded, as stated in the [Installation Blueprint](README.md#installation-blueprint).

### Network and Execution Order Protocol

To avoid startup crashes and missing library errors, your initial execution sequence must strictly follow these two distinct phases:

#### Phase 1: Dependency Acquisition (Internet Required)
1. Connect to your local internet network via Wi-Fi or Ethernet on the Raspberry Pi.
2. Execute all three primary project scripts once sequentially while connected to the internet:
   ```bash
   python3 0_open_button.py
   python3 1_open_YOLO_detection.py
   python3 2_open_QUESTIONNAIRE_ollama.py
   ```
   Note: This step forces the system to pull down all missing dependencies, model structures, and framework weights into your virtual environment.

#### Phase 2: Hardware Deployment (Local Camera Network)
1. Disconnect from the internet network once downloads finish.
2. Connect to the ESP32 Camera Wi-Fi network hosted by your local hardware capture card module.
3. Execute the unified system pipeline:
   ```bash
   python3 0_open_button.py
   ```
   The scripts will now successfully bind directly to the active hardware IP video stream using your local fallback parameters.
   
### Audio Input/Output Distortions

If the audio feedback in the earbuds becomes distorted or glitches, the issue is most likely caused by the USB-to-TRRS Audio Adapter. Please execute the following troubleshooting steps in order:

1. **Hardware Reset:** Disconnect and reconnect the USB-to-TRRS Audio Adapter before debugging or altering the programs.
2. **System Reset:** If the problem persists, reboot the Raspberry Pi 5.
3. **Software Updates:** Ensure the Raspberry Pi OS is fully updated (`sudo apt update && sudo apt upgrade`) to resolve any potential operating system audio configuration or driver conflicts.
