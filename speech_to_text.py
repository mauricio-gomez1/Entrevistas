import whisper
import os
from typing import Dict, Optional

class SpeechToText:
    def __init__(self, model_size: str = "base"):
        """
        Initialize the speech-to-text converter.
        Args:
            model_size: Size of the Whisper model ("tiny", "base", "small", "medium", "large")
        """
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_path: str) -> Dict:
        """
        Transcribe audio file to text.
        Args:
            audio_path: Path to the audio file
        Returns:
            Dictionary containing transcription results
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            # Transcribe audio
            result = self.model.transcribe(audio_path)
            
            return {
                'text': result['text'],
                'segments': result['segments'],
                'language': result.get('language', 'en')
            }
            
        except Exception as e:
            print(f"Error transcribing audio: {str(e)}")
            return {
                'text': '',
                'segments': [],
                'language': 'en'
            }

    def get_word_timestamps(self, segments: list) -> list:
        """
        Extract word-level timestamps from segments.
        Args:
            segments: List of segments from transcription
        Returns:
            List of words with their timestamps
        """
        words = []
        for segment in segments:
            start = segment['start']
            end = segment['end']
            text = segment['text'].strip()
            
            # Simple word splitting (can be improved with better tokenization)
            word_list = text.split()
            duration = end - start
            word_duration = duration / len(word_list)
            
            for i, word in enumerate(word_list):
                word_start = start + (i * word_duration)
                word_end = word_start + word_duration
                words.append({
                    'word': word,
                    'start': word_start,
                    'end': word_end
                })
        
        return words 