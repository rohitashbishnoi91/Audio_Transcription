import os
import pyttsx3
import wave
import contextlib

def create_test_audio():
    # Create test_files directory if it doesn't exist
    os.makedirs('test_files', exist_ok=True)
    
    # Initialize the text-to-speech engine
    engine = pyttsx3.init()
    
    # Set properties (optional)
    engine.setProperty('rate', 150)    # Speed of speech
    engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
    
    # Get available voices and set a clear voice
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'english' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    
    # Text to be spoken
    text = "Hello, this is a test audio file for speech recognition. The weather is nice today."
    
    # Save to file
    output_file = 'test_files/test_speech.wav'
    engine.save_to_file(text, output_file)
    engine.runAndWait()
    
    # Verify the file was created and get its duration
    if os.path.exists(output_file):
        with contextlib.closing(wave.open(output_file, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            print(f"Created test audio file: {output_file}")
            print(f"Duration: {duration:.2f} seconds")
            print(f"Sample rate: {rate} Hz")
            print(f"Text spoken: '{text}'")
    else:
        print("Error: Failed to create audio file")

if __name__ == '__main__':
    create_test_audio() 