import os
import sys
import time
import contextlib
import numpy as np
import sounddevice as sd

@contextlib.contextmanager
def suppress_stderr():
    """Context manager to suppress low-level C++ stderr logging (like ONNX schema warnings)."""
    try:
        null_fd = os.open(os.devnull, os.O_WRONLY)
        save_stderr = os.dup(2)
        os.dup2(null_fd, 2)
        yield
    except Exception:
        yield
    finally:
        try:
            os.dup2(save_stderr, 2)
            os.close(null_fd)
            os.close(save_stderr)
        except Exception:
            pass

def find_input_device():
    """Find the best input audio device index, prioritizing Kinect."""
    try:
        devices = sd.query_devices()
        # 1. Prioritize kinect_clean
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0 and "kinect_clean" in d['name'].lower():
                return i
        # 2. Try kinect_mono
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0 and "kinect_mono" in d['name'].lower():
                return i
        # 3. Try Kinect USB Audio
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0 and "kinect" in d['name'].lower():
                return i
        # 4. Fallback to default
        default_idx = sd.default.device[0]
        if default_idx >= 0:
            return default_idx
        # 5. First device with input channels
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                return i
    except Exception as e:
        print(f"Error querying audio devices: {e}", file=sys.stderr)
    return None

def main():
    print("=== Mina Assistant Wake Word Daemon (openWakeWord) ===")
    print("This daemon runs locally, requires NO API keys, and uses standard audio devices.")
    print("Active Wake Words (Chaves): 'alexa' and 'hey jarvis'\n")
    
    device_idx = find_input_device()
    if device_idx is not None:
        try:
            device_name = sd.query_devices(device_idx)['name']
            print(f"Selected audio input device index: {device_idx} ({device_name})")
        except Exception:
            print(f"Selected audio input device index: {device_idx}")
    else:
        print("Warning: No audio input device found!", file=sys.stderr)
        
    print("Initializing openWakeWord models...")
    try:
        with suppress_stderr():
            import openwakeword.utils
            from openwakeword.model import Model
            # Auto-download models if missing
            openwakeword.utils.download_models()
            model = Model(wakeword_models=["alexa", "hey_jarvis"], inference_framework="onnx")
    except Exception as e:
        print(f"Failed to initialize openWakeWord: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nStarting background listener...")
    print(">>> [ACTIVE] Listening for 'alexa' or 'hey jarvis'...")
    print("Press Ctrl+C to terminate the daemon.\n")

    # Generate the chime once to reuse
    sample_rate = 16000
    duration = 0.25
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    wave = 0.5 * np.sin(2 * np.pi * 880 * t) + 0.25 * np.sin(2 * np.pi * 1760 * t)
    envelope = np.exp(-12 * t)
    audio = (wave * envelope * 32767).astype(np.int16)

    def audio_callback(indata, frames, time_info, status):
        audio_frame = indata[:, 0]
        prediction = model.predict(audio_frame)
        
        for name, prob in prediction.items():
            if prob > 0.6:
                print(f"🎉 [DETECTED: '{name}'] - Playing chime...")
                sd.play(audio, samplerate=16000)

    try:
        # Start input stream at 16kHz using selected device
        with sd.InputStream(device=device_idx, samplerate=16000, channels=1, dtype='int16', blocksize=1280, callback=audio_callback):
            while True:
                sd.sleep(100)
    except KeyboardInterrupt:
        print("\nStopping wake word daemon...")
    except Exception as e:
        print(f"Fatal error in daemon stream: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
