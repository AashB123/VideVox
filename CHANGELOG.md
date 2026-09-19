# Changelog

All **notable** changes to this project will be documented in this file.

## - 2026-09-18

### Added
- **Double-Streaming Architecture**: Integrated `ollama_tts_stream(prompt)` to fetch real-time text chunks word-by-word from the `SmolVLM2-500M-Video-Instruct-GGUF:Q8_0` model [2026-09-18].
- **Sentence Boundary Cues**: Enabled immediate sentence-by-sentence vocalizations triggered instantly by punctuation marks, maximizing speech efficiency [2026-09-18].

### Changed
- **On-the-Fly Audio Pipeline**: Rewrote `speak()` to stream raw audio fragments directly to `aplay` instead of processing full paragraph strings sequentially [2026-09-18].
- **Conversational Handoff Windows**: Shortened the live recording window from 5 seconds to a crisp 3 seconds to eliminate dead silence and robotic delays [2026-09-18].
