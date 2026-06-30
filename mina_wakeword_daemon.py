import os
import sys
import time
import numpy as np
import sounddevice as sd
from openwakeword.model import Model

def play_plim():
    """Generate and play a pleasant synthetic chime (plim) sound."""
    sample_rate = 16000
    duration = 0.25  # 250 ms
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Chime mixing high frequencies (880Hz and 1760Hz)
    wave = 0.5 * np.sin(2 * np.pi * 880 * t) + 0.25 * np.sin(2 * np.pi * 1760 * t)
    
    # Exponential decay envelope for a smooth fade out
    envelope = np.exp(-12 * t)
    audio = (wave * envelope * 32767).astype(np.int16)
    
    try:
        sd.play(audio, samplerate=sample_rate)
        sd.wait()
    except Exception as e:
        print(f"Error playing chime: {e}", file=sys.stderr)

def main():
    print("=== Mina Assistant Wake Word Daemon (openWakeWord) ===")
    print("This daemon runs locally, requires NO API keys, and uses standard audio devices.")
    print("Active Wake Words (Chaves): 'alexa' and 'hey jarvis'\n")
    
    print("Initializing openWakeWord models...")
    try:
        model = Model(wakeword_models=["alexa", "hey_jarvis"], inference_framework="onnx")
    except Exception as e:
        print(f"Failed to initialize openWakeWord: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nStarting background listener...")
    print(">>> [ACTIVE] Listening for 'alexa' or 'hey jarvis'...")
    print("Press Ctrl+C to terminate the daemon.\n")

    # Callback to process input audio chunks
    def callback(indata, frames, time, status):
        if status:
            print(f"Audio stream status warning: {status}", file=sys.stderr)
        
        # Extract mono channel and feed to openWakeWord
        audio_frame = indata[:, 0]
        prediction = model.predict(audio_frame)
        
        for name, prob in prediction.items():
            if prob > 0.6:
                print(f"🎉 [WAKE WORD DETECTED] Key: '{name}' | Confidence: {prob:.2f}")
                # Play the chime in a non-blocking thread to avoid blocking the audio callback
                sd.play(audio, samplerate=16000) # Quick playback

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
                # Play chime directly using sounddevice (non-blocking write or output stream)
                # Since output stream is not active, we can play it asynchronously
                sd.play(audio, samplerate=16000)

    try:
        # Start input stream at 16kHz
        with sd.InputStream(samplerate=16000, channels=1, dtype='int16', blocksize=1280, callback=audio_callback):
            while True:
                sd.sleep(100)
    except KeyboardInterrupt:
        print("\nStopping wake word daemon...")
    except Exception as e:
        print(f"Fatal error in daemon stream: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
