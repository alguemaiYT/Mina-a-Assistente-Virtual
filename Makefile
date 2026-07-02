.DEFAULT_GOAL := help

PYTHON ?= python
PIP ?= $(PYTHON) -m pip
CC ?= gcc
STT_LINUX ?= libs/stt/libstt.so
STT_WINDOWS ?= libs/stt/stt.dll

.PHONY: help install install-mac run run-fullscreen run-studio lint format sort-imports check test install-deps compile apicomm clean stt-linux stt-windows all

help:
	@echo "Available targets:"
	@echo "  install        Install Python dependencies"
	@echo "  install-mac    Install macOS-specific dependencies"
	@echo "  run            Launch the GUI"
	@echo "  run-fullscreen Launch the GUI in fullscreen"
	@echo "  run-studio     Launch the GUI in studio/layout mode"
	@echo "  lint           Run Flake8"
	@echo "  format         Run Black"
	@echo "  sort-imports   Run isort"
	@echo "  check          Run python -m compileall to validate syntax"
	@echo "  test           Alias for check"
	@echo "  install-deps   Install system deps (Debian/Ubuntu)"
	@echo "  compile        Builds apicomm"
	@echo "  apicomm        Compile c_src/apicomm.c"
	@echo "  stt-linux      Build libs/stt/libstt.so"
	@echo "  stt-windows    Build libs/stt/stt.dll"
	@echo "  all            install-deps + compile (Debian/Ubuntu helper)"

install:
	$(PIP) install -r requirements.txt

install-mac:
	$(PIP) install -r requirements_mac.txt

run:
	$(PYTHON) main_gui.py

run-fullscreen:
	$(PYTHON) main_gui.py -f

run-studio:
	$(PYTHON) main_gui.py -s

run-tts:
	$(PYTHON) -m uvicorn tts_api.main:app --host 0.0.0.0 --port 8000

lint:
	$(PYTHON) -m flake8 .

format:
	$(PYTHON) -m black .

sort-imports:
	$(PYTHON) -m isort .

check:
	$(PYTHON) -m compileall main_gui.py src

test: check

install-deps:
	@echo "Installing system dependencies on Debian/Ubuntu..."
	apt-get update
	apt-get install -y libcjson-dev libcurl4-openssl-dev

compile: apicomm

apicomm: c_src/apicomm.c
	@echo "Compiling apicomm..."
	$(CC) -O2 -march=native -Wall -Wextra -o apicomm c_src/apicomm.c -lcurl -lcjson
	@ls -lh apicomm

clean:
	@echo "Cleaning binaries..."
	rm -f apicomm stt *.o

stt-linux:
	@echo "Building STT helper for Linux..."
	$(CC) -shared -fPIC c_src/stt.c -o $(STT_LINUX) -lportaudio -lcurl

stt-windows:
	@echo "Building STT helper for Windows..."
	$(CC) -shared -fPIC c_src/stt.c -o $(STT_WINDOWS) -lportaudio -lcurl

all: install-deps compile
