import io
import tempfile
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment


def text_to_speech(text: str) -> bytes:
    """Convert text to speech and return audio bytes."""
    tts = gTTS(text=text, lang='en', slow=False)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer.read()

def speech_to_text(audio_bytes: bytes) -> str:
    """Convert recorded audio bytes to text."""
    import tempfile
    import os
    from pydub import AudioSegment
    recognizer = sr.Recognizer()
    
    # Save raw audio to temp file
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio_bytes)
        mp3_path = f.name
    
    # Convert to WAV
    wav_path = mp3_path.replace(".mp3", ".wav")
    audio_segment = AudioSegment.from_file(mp3_path)
    audio_segment.export(wav_path, format="wav")
    
    # Transcribe
    with sr.AudioFile(wav_path) as source:
        audio = recognizer.record(source)
    
    # Cleanup
    os.remove(mp3_path)
    os.remove(wav_path)
    
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return "Speech recognition service unavailable."