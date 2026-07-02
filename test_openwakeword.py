import numpy as np
import sounddevice as sd
from openwakeword.model import Model
import sys

def main():
    print("=== Stand-alone openWakeWord Test ===")
    
    # 1. Initialize openwakeword with default models
    print("Initializing openWakeWord models (downloading/loading if needed)...")
    try:
        model = Model(wakeword_models=["alexa", "hey_jarvis"])
    except Exception as e:
        print(f"Failed to initialize openWakeWord: {e}")
        sys.exit(1)
        
    print("\nStarting listener...")
    print(">>> [LISTENING] Speak 'alexa' or 'hey jarvis' to test!")
    print("Press Ctrl+C to stop.\n")

    # Callback receives chunk of 1280 samples (80ms at 16kHz)
    def callback(indata, frames, time, status):
        if status:
            print(f"Status warning: {status}", file=sys.stderr)
        audio_frame = indata[:, 0]
        prediction = model.predict(audio_frame)
        
        for name, prob in prediction.items():
            if prob > 0.6:
                print(f"🎉 [WAKE WORD DETECTED] !!! ({name} | confidence: {prob:.2f})")

    try:
        with sd.InputStream(samplerate=16000, channels=1, dtype='int16', blocksize=1280, callback=callback):
            while True:
                sd.sleep(100)
    except KeyboardInterrupt:
        print("\nStopping listener...")
    except Exception as e:
        print(f"Error during audio stream: {e}")

if __name__ == "__main__":
    main()
