from faster_whisper import WhisperModel
import os
from typing import Dict, Optional

class SpeechToText:
    def __init__(self, model_size: str = "base"):
        """
        Initialize the speech-to-text converter.
        Args:
            model_size: Size of the Whisper model ("tiny", "base", "small", "medium", "large")
        """
        try:
            # Use faster-whisper for better performance and compatibility
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
            self.model_available = True
        except Exception as e:
            print(f"Error loading Whisper model: {str(e)}")
            self.model = None
            self.model_available = False

    def transcribe(self, audio_path: str) -> Dict:
        """
        Transcribe audio file to text.
        Args:
            audio_path: Path to the audio file
        Returns:
            Dictionary containing transcription results
        """
        if not self.model_available:
            print("Speech-to-text model not available")
            return {
                'text': '',
                'segments': [],
                'language': 'es'
            }
            
        if not os.path.exists(audio_path):
            print(f"Audio file not found: {audio_path}")
            return {
                'text': '',
                'segments': [],
                'language': 'es'
            }

        try:
            # Transcribe audio using faster-whisper
            segments, info = self.model.transcribe(audio_path, beam_size=5)
            
            # Convert segments to list and extract text
            segments_list = []
            full_text = ""
            
            for segment in segments:
                segment_dict = {
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text
                }
                segments_list.append(segment_dict)
                full_text += segment.text
            
            return {
                'text': full_text.strip(),
                'segments': segments_list,
                'language': info.language
            }
            
        except Exception as e:
            print(f"Error transcribing audio: {str(e)}")
            return {
                'text': '',
                'segments': [],
                'language': 'es'
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