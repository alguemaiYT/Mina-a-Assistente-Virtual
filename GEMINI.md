# GEMINI.md - Project Context: Mina - a Assistente Virtual do G.E.R.A.

## Project Overview
**Mina** is an interactive virtual assistant designed for both desktop and edge devices (Raspberry Pi, Orange Pi). It features a visually expressive GUI with emotional animations, integrated Speech-to-Text (STT), Text-to-Speech (TTS), and a flexible chat backend architecture.

### Key Technologies
- **Main Logic:** Python 3.9+ with `asyncio`.
- **GUI Framework:** PyQt5 & QML for the frontend, using `qasync` to unify the event loop.
- **Native Components:** C-based helpers for high-performance I/O:
  - `apicomm.c`: C backend for communication.
  - `stt.c`: PortAudio-based STT helper.
- **Edge Components:** Rust-based client (`edge_opi_client/`) for hardware integration.
- **AI/LLM:** Supports local binary execution or cloud APIs (e.g., Groq).
- **Wake Word:** Picovoice Porcupine for keyword detection ("Abacaxi").
- **TTS:** Custom API support (`tts_api/`) with ONNX models (Kokoro).

---

## Building and Running

### Prerequisites
- **System Dependencies (Linux/Debian):**
  ```bash
  sudo apt-get install libcjson-dev libcurl4-openssl-dev libportaudio2
  ```

### Key Commands
- **Install Python Dependencies:** `make install`
- **Run GUI (Standard):** `make run`
- **Run GUI (Fullscreen):** `make run-fullscreen`
- **Run GUI (Studio/Layout Mode):** `make run-studio`
- **Compile Native Components:** `make compile` (builds `apicomm`)
- **Build STT Helper:** `make stt-linux` (builds `libs/stt/libstt.so`)
- **Linting & Formatting:** `make lint`, `make format`, `make sort-imports`

## Automatic Binary Management
The project features an automatic compilation system for native binaries (`apicomm` and `stt` libraries).
- **Storage:** Binaries are stored in architecture-specific folders:
  - Executables: `bin/<arch>/` (e.g., `bin/x86_64/apicomm`, `bin/armv7l/apicomm`)
  - Shared Libraries: `libs/<arch>/` (e.g., `libs/x86_64/libstt.so`, `libs/armv7l/libstt.so`)
- **Lifecycle:** Upon initialization of `ChatBridge` or `STTClient`, the `BinaryManager` checks if the required binary exists for the current architecture. If missing, it attempts to trigger `make` to compile it on the fly.
- **Manual Trigger:** You can manually compile for the current architecture using `make compile`.

---

## Architecture & Data Flow

### The "Chunk" Protocol
Mina uses a specialized streaming protocol to synchronize speech, text, and facial animations. Every AI response is processed as a series of chunks:
`CHUNK|delay_ms|emotion|text`
- **delay_ms:** Time to wait before/during the chunk display.
- **emotion:** One of 22 valid emotions (e.g., `happy`, `thinking`, `neutral`).
- **text:** The actual text to display and speak.

### Module Responsibilities
- `src/display/`: Pure UI logic. Python bridge (`GuiDisplayModel`) communicates with QML.
- `src/utils/`: Side-effect heavy logic.
  - `chat_bridge.py`: Manages LLM interaction (Binary vs. Groq).
  - `config_manager.py`: Centralized configuration access.
  - `stt_client.py` / `tts_client.py`: Wrappers for speech services.
  - `wake_word_listener.py`: Handles "Abacaxi" wake word detection.
  - `vad_monitor.py`: Voice Activity Detection (VAD) to detect when the user stops speaking.
- `assets/emojis/`: GIFs named exactly after valid emotions used by the QML frontend.
- `libs/`: Shared libraries for native STT and communication.

---

## Development Conventions

- **Language:** User-facing text and AI persona must be in **Brazilian Portuguese (PT-BR)**.
- **Async Safety:** Always use `asyncio` for I/O operations. Wrap the Qt loop with `qasync`.
- **Configuration:** Never read `config.json` directly; use `ConfigManager`.
- **Emotional Palette:** When modifying prompts or AI behavior, ensure responses adhere to the valid emotion keys found in `assets/emojis/`.
- **Native Logic:** If modifying `stt.c` or `apicomm.c`, you must run `make compile` or `make stt-linux` to refresh the shared libraries.

---

## Common Pitfalls
- **PortAudio Monopolization:** Ensure no other applications are using the microphone if STT fails.
- **Binary Compatibility:** Shared libraries in `libs/` must match the host architecture (x86_64 vs. ARM).
- **Environment Variables:** Ensure `GROQ_API_KEY` is set if using the Groq backend.
