## Troubleshooting and Hardware Setup

If you encounter connection drops, dependency errors, or network timeout issues, follow this step-by-step verification pipeline to reset the runtime environment.

### Network and Execution Order Protocol

To avoid startup crashes and missing library errors, your initial execution sequence must strictly follow these two distinct phases:

#### Phase 1: Dependency Acquisition (Internet Required)
1. Connect to your local internet network via Wi-Fi or Ethernet on the Raspberry Pi.
2. Execute all three primary project scripts once sequentially while connected to the internet:
   ```bash
   python3 OPEN_SOURCING_CODE/0_open_button.py
   python3 OPEN_SOURCING_CODE/1_open_YOLO_detection.py
   python3 OPEN_SOURCING_CODE/2_open_QUESTIONNAIRE_ollama.py
   ```
   Note: This step forces the system to pull down all missing dependencies, model structures, and framework weights into your virtual environment.

#### Phase 2: Hardware Deployment (Local Camera Network)
1. Disconnect from the internet network once downloads finish.
2. Connect to the ESP32 Camera Wi-Fi network hosted by your local hardware capture card module.
3. Execute the unified system pipeline:
   ```bash
   python3 OPEN_SOURCING_CODE/0_open_button.py
   ```
   The scripts will now successfully bind directly to the active hardware IP video stream using your local fallback parameters.
