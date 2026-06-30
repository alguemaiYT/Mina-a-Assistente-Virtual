import os
import sys
import time
import contextlib
import queue
import threading
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
    """Find the best input audio device index, prioritizing raw Kinect hardware."""
    try:
        devices = sd.query_devices()
        # 1. Prioritize raw Kinect USB Audio
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0 and "kinect usb audio" in d['name'].lower():
                return i
        # 2. Try any Kinect device
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0 and "kinect" in d['name'].lower():
                return i
        # 3. Fallback to default
        default_idx = sd.default.device[0]
        if default_idx >= 0:
            return default_idx
        # 4. First device with input channels
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
            device_info = sd.query_devices(device_idx)
            device_name = device_info['name']
            print(f"Selected audio input device index: {device_idx} ({device_name})")
        except Exception:
            device_name = "Unknown"
            print(f"Selected audio input device index: {device_idx}")
    else:
        print("Warning: No audio input device found!", file=sys.stderr)
        sys.exit(1)
        
    is_raw_kinect = "kinect usb audio" in device_name.lower() or "hw:3,0" in device_name.lower()
    
    if is_raw_kinect:
        channels = 4
        dtype = 'int32'
        print(">>> RAW Kinect Mode Enabled (4 channels, 32-bit downmixed to 16-bit PCM in real-time)")
    else:
        channels = 1
        dtype = 'int16'
        print(">>> Standard Mode Enabled (1 channel, 16-bit PCM)")
        
    print("\nInitializing openWakeWord models...")
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

    # Thread-safe queue to pass audio frames from callback thread to processing worker thread
    audio_queue = queue.Queue()
    stop_event = threading.Event()

    def audio_callback(indata, frames, time_info, status):
        if status:
            # We print status warnings to stderr, but avoid logging full traces in real-time
            pass
            
        if is_raw_kinect:
            # Extract channel 0 and convert 32-bit to 16-bit PCM
            audio_frame = (indata[:, 0] // 65536).astype(np.int16)
        else:
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
