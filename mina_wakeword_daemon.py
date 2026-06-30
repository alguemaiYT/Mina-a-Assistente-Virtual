import os
import sys
import time
import contextlib
import queue
import threading
import numpy as np

# Force PulseAudio server socket path on Linux before importing sounddevice
if sys.platform.startswith("linux"):
    os.environ["PULSE_SERVER"] = "unix:/var/run/pulse/native"

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
    """Find the best input audio device index, prioritizing PulseAudio on Linux."""
    try:
        devices = sd.query_devices()
        # 1. On Linux, search for "pulse" device
        if sys.platform.startswith("linux"):
            for i, d in enumerate(devices):
                if d['max_input_channels'] > 0 and d['name'].lower() == "pulse":
                    return i
        # 2. Fallback to default
        default_idx = sd.default.device[0]
        if default_idx >= 0:
            return default_idx
        # 3. First device with input channels
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                return i
    except Exception as e:
        print(f"Error querying audio devices: {e}", file=sys.stderr)
    return None

def main():
    print("=== Mina Assistant Wake Word Daemon (openWakeWord + PulseAudio) ===")
    print("This daemon runs locally, requires NO API keys, and uses standard audio devices.")
    print("Active Wake Words (Chaves): 'alexa' and 'hey jarvis'\n")
    
    device_idx = find_input_device()
    if device_idx is not None:
        try:
            device_info = sd.query_devices(device_idx)
            device_name = device_info['name']
            print(f"Selected audio input device index: {device_idx} ({device_name})")
        except Exception:
            device_name = "Unknown"
            print(f"Selected audio input device index: {device_idx}")
    else:
        print("Warning: No audio input device found!", file=sys.stderr)
        sys.exit(1)
        
    # PulseAudio handles all channel mixing, format conversion (S32_LE to S16_LE)
    # and hardware interfacing in the background!
    channels = 1
    dtype = 'int16'
    print(">>> Mode: 1 channel, 16-bit PCM (Resampled and downmixed by PulseAudio/System)")
        
    print("\nInitializing openWakeWord models...")
    try:
        # Only suppress stderr during the imports to silence C++ schema registration logs
        with suppress_stderr():
            import openwakeword.utils
            from openwakeword.model import Model
            
        # Run downloads and model initialization outside suppress_stderr block
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

    # Thread-safe queue to pass audio frames from callback thread to processing worker thread
    audio_queue = queue.Queue()
    stop_event = threading.Event()

    def audio_callback(indata, frames, time_info, status):
        if status:
            pass
        # Indata is already 1 channel, 16-bit PCM (int16)
        audio_frame = indata[:, 0].copy()
        audio_queue.put(audio_frame)

    def processing_worker():
        while not stop_event.is_set():
            try:
                # Retrieve frame from queue with a short timeout
                audio_frame = audio_queue.get(timeout=0.2)
            except queue.Empty:
                continue
                
            # Perform inference on worker thread
            prediction = model.predict(audio_frame)
            
            for name, prob in prediction.items():
                if prob > 0.6:
                    print(f"🎉 [DETECTED: '{name}'] - Playing chime...")
                    try:
                        sd.play(audio, samplerate=16000)
                    except Exception as e:
                        print(f"Chime error: {e}", file=sys.stderr)
            
            audio_queue.task_done()

    # Launch the processing worker thread
    worker_thread = threading.Thread(target=processing_worker, daemon=True)
    worker_thread.start()

    try:
        # Start input stream using selected device
        with sd.InputStream(device=device_idx, samplerate=16000, channels=channels, dtype=dtype, blocksize=1280, callback=audio_callback):
            while True:
                sd.sleep(100)
    except KeyboardInterrupt:
        print("\nStopping wake word daemon...")
    finally:
        stop_event.set()
        worker_thread.join(timeout=1.0)
        print("Cleaned up resources. Goodbye!")

if __name__ == "__main__":
    main()
