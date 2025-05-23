import wave
import numpy as np
import os

# Create dummy WAV file function
def create_dummy_wav(filepath, duration=0.1, freq=440, sample_rate=44100):
    # Ensure the directory for the file exists if it's not the current directory
    dir_name = os.path.dirname(filepath)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
        
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    # Generate a sine wave
    audio_data = (np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)
    
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)  # mono
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())
    print(f"Successfully created dummy WAV file: {filepath}")

if __name__ == "__main__":
    create_dummy_wav("e2e_test_audio.wav")
