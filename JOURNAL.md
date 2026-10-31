# Journal

All **notable** changes to this project will be documented in this file.

## - 2026-10-19

### Added
- **Asynchronous Execution Architecture**: Upgraded to full asynchronous Python usage (`asyncio`, `aiohttp`, and `async_subprocess_exec`) across the entire VLM questionnaire pipeline to maximize performance and non-blocking I/O [2026-10-19].

### Changed
- **Inference Backend Migration**: Replaced the external Ollama framework with a localized, compiled `llama.cpp` `llama-server` subprocess, locked to physical CPU cores with strict batch and context bounds [2026-10-19].
- **Streamlined Code & Time Efficiency**: Completely restructured the VLM questionnaire and audio streaming pipeline for instantaneous server response processing, pre-flight asset validation, and dynamic audio device auto-detection [2026-10-19].

## - 2026-09-18

<img width="600" height="800" alt="VideVox_Thumbnail" src="https://github.com/user-attachments/assets/e66d73ab-449b-4db6-8a25-301bffbefbf9" />

### Added
- **Double-Streaming Architecture**: Integrated `ollama_tts_stream(prompt)` to fetch real-time text chunks word-by-word from the `SmolVLM2-500M-Video-Instruct-GGUF:Q8_0` model [2026-09-18].
- **Sentence Boundary Cues**: Enabled immediate sentence-by-sentence vocalizations triggered instantly by punctuation marks, maximizing speech efficiency [2026-09-18].

### Changed
- **On-the-Fly Audio Pipeline**: Rewrote `speak()` to stream raw audio fragments directly to `aplay` instead of processing full paragraph strings sequentially [2026-09-18].
- **Conversational Handoff Windows**: Shortened the live recording window from 5 seconds to a crisp 3 seconds to eliminate dead silence and robotic delays [2026-09-18].
