import wave
import numpy as np

def main():
    try:
        w = wave.open('/tmp/kinect_test.wav', 'rb')
        params = w.getparams()
        print(f"WAV Parameters: {params}")
        frames = w.readframes(w.getnframes())
        data = np.frombuffer(frames, dtype=np.int32)
        
        num_channels = params.nchannels
        data = data.reshape(-1, num_channels)
        print("\n--- Audio Levels per channel ---")
        for ch in range(num_channels):
            ch_data = data[:, ch]
            max_val = np.max(np.abs(ch_data))
            rms = np.sqrt(np.mean(ch_data.astype(np.float64)**2))
            print(f"Channel {ch}: Peak = {max_val} | RMS = {rms:.1f}")
            
    except Exception as e:
        print(f"Error analyzing WAV: {e}")

if __name__ == "__main__":
    main()
