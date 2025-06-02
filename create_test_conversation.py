import os
import pyttsx3
import wave
import contextlib
import time

def create_test_conversation():
    # Create test_files directory if it doesn't exist
    os.makedirs('test_files', exist_ok=True)
    
    # Initialize the text-to-speech engine
    engine = pyttsx3.init()
    
    # Set properties for better quality
    engine.setProperty('rate', 150)    # Speed of speech
    engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
    
    # Get available voices
    voices = engine.getProperty('voices')
    
    # Find two different voices (preferably male and female)
    voice1 = None
    voice2 = None
    for voice in voices:
        if not voice1 and 'english' in voice.name.lower():
            voice1 = voice
        elif not voice2 and 'english' in voice.name.lower() and voice.id != voice1.id:
            voice2 = voice
            break
    
    if not voice1 or not voice2:
        print("Could not find two different voices. Using default voices.")
        voice1 = voices[0]
        voice2 = voices[1] if len(voices) > 1 else voices[0]
    
    # Conversation script
    conversation = [
        ("SPEAKER_1", "Hello, how are you today?"),
        ("SPEAKER_2", "I'm doing well, thank you for asking. How about you?"),
        ("SPEAKER_1", "I'm great! I'm working on an audio transcription project."),
        ("SPEAKER_2", "That sounds interesting! What kind of features are you implementing?"),
        ("SPEAKER_1", "We're adding speaker diarization to identify different speakers in the audio."),
        ("SPEAKER_2", "That's fascinating! How does it work?"),
        ("SPEAKER_1", "It uses machine learning to distinguish between different speakers based on their voice characteristics."),
        ("SPEAKER_2", "That's really impressive technology. Good luck with your project!")
    ]
    
    # Create separate audio files for each speaker
    speaker1_file = 'test_files/speaker1.wav'
    speaker2_file = 'test_files/speaker2.wav'
    
    # Generate audio for each speaker
    print("Generating audio for Speaker 1...")
    engine.setProperty('voice', voice1.id)
    for speaker, text in conversation:
        if speaker == "SPEAKER_1":
            engine.save_to_file(text, speaker1_file)
            engine.runAndWait()
            time.sleep(0.5)  # Small pause between sentences
    
    print("Generating audio for Speaker 2...")
    engine.setProperty('voice', voice2.id)
    for speaker, text in conversation:
        if speaker == "SPEAKER_2":
            engine.save_to_file(text, speaker2_file)
            engine.runAndWait()
            time.sleep(0.5)  # Small pause between sentences
    
    # Combine the audio files (we'll use a simple concatenation for testing)
    from pydub import AudioSegment
    
    # Load the audio files
    audio1 = AudioSegment.from_wav(speaker1_file)
    audio2 = AudioSegment.from_wav(speaker2_file)
    
    # Add a small silence between speakers
    silence = AudioSegment.silent(duration=500)  # 500ms silence
    
    # Combine the audio
    combined = AudioSegment.empty()
    for speaker, _ in conversation:
        if speaker == "SPEAKER_1":
            combined += audio1 + silence
        else:
            combined += audio2 + silence
    
    # Export the combined audio
    output_file = 'test_files/test_conversation.wav'
    combined.export(output_file, format='wav')
    
    # Clean up individual speaker files
    os.remove(speaker1_file)
    os.remove(speaker2_file)
    
    # Verify the file was created and get its duration
    if os.path.exists(output_file):
        with contextlib.closing(wave.open(output_file, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            print(f"\nCreated test conversation file: {output_file}")
            print(f"Duration: {duration:.2f} seconds")
            print(f"Sample rate: {rate} Hz")
            print("\nConversation script:")
            for speaker, text in conversation:
                print(f"{speaker}: {text}")
    else:
        print("Error: Failed to create audio file")

if __name__ == '__main__':
    create_test_conversation() 