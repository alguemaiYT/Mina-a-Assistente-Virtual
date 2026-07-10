# Guidelines for AI Agents

Welcome, AI Agent. This document provides universal guidelines, architectural constraints, and notes on the project's state. Please adhere to these rules when interacting with or modifying the codebase.

## 1. Project Overview & Architecture

- **Description:** A Python-based voice interface application featuring wake word detection (using Picovoice/pvporcupine) and Text-to-Speech (TTS) capabilities utilizing ONNX models.
- **Repository Architecture:**
  - `src/display/`: Strictly for UI and Python bridge (`GuiDisplayModel`). The GUI layout wraps screen elements inside a `rotationWrapper` in `gui_display.qml` to honor dynamic screen rotation parameters (`-g`). Time-sensitive UI calculations should utilize the NTP time offset synchronization (`src/utils/ntp_sync.py`) stored in `memory.db`.
  - `src/utils/`: Handles side-effects (STT, Chat, Config, NTP).
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
- **Subprocesses:**
  - When spawning Python subprocesses (especially in tests), dynamically resolve the `cwd` path using `os.path.dirname` rather than hardcoded absolute paths to prevent file not found errors in varying execution environments.
- **Networking/HTTP:**
  - For `aiohttp` usage, reuse a single `ClientSession` instance across requests to benefit from connection pooling, rather than instantiating a new session per request, to avoid unnecessary TCP/TLS handshake latency.

## 3. Testing & Code Quality

- **Testing Framework:** The project uses `pytest` for testing.
- **Running Tests:**
  - Running the pytest suite requires setting the `PYTHONPATH` to the project root to resolve local module imports.
  - Use `xvfb-run` for headless UI testing (e.g., `PYTHONPATH=. xvfb-run pytest tests/`).
  - The test suite requires `opencv-python-headless` and system Qt platform dependencies (`libxcb-cursor0`, `libxcb-xinerama0`, `qt5-qmake`, `qtbase5-dev`) to avoid 'xcb' plugin errors during GUI tests.
  - Example test command: `PYTHONPATH=. xvfb-run pytest tests/test_all.py`
- **Linting:** The project uses `flake8` for code linting.
- **Continuous Integration:** CI/CD and development infrastructure are in place. Any architectural modifications should consider the impact on test pipelines.

## 4. Current Technical Debt & Notes

- **Hardcoded Configuration:** Recent efforts have removed hardcoded fallback IPs (e.g., in `academic_db.py`). Please avoid introducing hardcoded network addresses or paths. Use `.env` or configurations for dynamic values.
- **Database Hygiene:** Databases are no longer tracked in the repository to maintain cleanliness.
- **Performance:** Performance optimizations (like TTS normalization, TTS HTTP session pooling, DB init caching, and DB sync batching logic) have been made. Be mindful of introducing performance regressions, particularly in the hot loops (like canvas drag/resize I/O or Wake Word processing).
- **Performance Optimization Boundaries:** Always run lint/tests before creating a PR, add explanatory comments, and document performance impact. Ask before adding dependencies or making architectural changes. Never modify project config files without instruction, make breaking changes, optimize prematurely, or sacrifice readability.
- **Critical Learnings Journal:** Maintain a critical learnings journal at `.jules/bolt.md` using the format `## YYYY-MM-DD - [Title] \n **Learning:** [Insight] \n **Action:** [How to apply next time]` to document codebase-specific performance patterns and surprising edge cases.

## 5. Architectural Updates (2026-07-09)

- **NTP Sync & Timekeeping:** The system now incorporates persistent NTP time offset synchronization (`src/utils/ntp_sync.py`). The calculated offset is stored in `memory.db` to ensure accuracy even upon offline reboots. Agents must utilize this offset when time-sensitive calculations are required.
- **UI & Display Architecture:** The GUI layout now wraps screen elements, such as the `idleScreen`, inside a `rotationWrapper` within `src/display/gui_display.qml`. This ensures compliance with dynamic screen rotation parameters (`-g` flags). Agents modifying visual components must place them correctly within this hierarchical flow.
- **Performance:** JSON token parsing and database initialization checks have been optimized. Agents should be mindful of modifying these data parsing paths to avoid regressions in performance.
