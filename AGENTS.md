# Guidelines for AI Agents

Welcome, AI Agent. This document provides universal guidelines, architectural constraints, and notes on the project's state. Please adhere to these rules when interacting with or modifying the codebase.

## 1. Project Overview & Architecture

- **Description:** A Python-based voice interface application featuring wake word detection (using Picovoice/pvporcupine) and Text-to-Speech (TTS) capabilities utilizing ONNX models.
- **Repository Architecture:**
  - `src/display/`: Strictly for UI and Python bridge (`GuiDisplayModel`).
  - `src/utils/`: Handles side-effects (STT, Chat, Config).
  - **Frontend Layout:** Managed via `src/display/gui_display.qml`.
- **Frameworks & Libraries:**
  - The project uses **PyQt5** and QML for its graphical user interface components.
  - Python dependencies are managed via `requirements.txt`.
- **Databases:**
  - SQLite databases (e.g., `academic.db`, `memory.db`) are ignored in Git (`config/*.db` is tracked in `.gitignore`) and should not be directly tracked or hardcoded in patches.

## 2. Technical Guidelines & Protocols

- **TTS / Animation Protocol:**
  - AI responses and QML facial animations must strictly follow the `CHUNK|delay|emotion|text` protocol to maintain synchronization.
- **System Audio Dependencies:**
  - System audio dependencies, such as `portaudio19-dev`, must be installed via `apt-get` for audio-related modules to function properly during tests.

## 3. Testing & Code Quality

- **Testing Framework:** The project uses `pytest` for testing.
- **Running Tests:**
  - Running the pytest suite requires setting the `PYTHONPATH` to the project root to resolve local module imports.
  - Example test command: `PYTHONPATH=. python -m pytest tests/test_all.py`
- **Linting:** The project uses `flake8` for code linting.
- **Continuous Integration:** CI/CD and development infrastructure are in place. Any architectural modifications should consider the impact on test pipelines.

## 4. Current Technical Debt & Notes

- **Hardcoded Configuration:** Recent efforts have removed hardcoded fallback IPs (e.g., in `academic_db.py`). Please avoid introducing hardcoded network addresses or paths. Use `.env` or configurations for dynamic values.
- **Database Hygiene:** Databases are no longer tracked in the repository to maintain cleanliness.
- **Performance:** Performance optimizations (like TTS normalization and DB sync logic) have been made. Be mindful of introducing performance regressions, particularly in the hot loops (like canvas drag/resize I/O or Wake Word processing).
