import streamlit as st
import os
from resume_parser import ResumeParser

# Try to import optional modules
try:
    from facial_emotion import FacialEmotionAnalyzer
    FACIAL_EMOTION_AVAILABLE = True
except Exception as e:
    st.warning(f"Analsis facial no disponible: {str(e)}")
    FACIAL_EMOTION_AVAILABLE = False
    FacialEmotionAnalyzer = None

from voice_analysis import VoiceAnalyzer
from speech_to_text import SpeechToText
from content_matcher import ContentMatcher
from interview_bot import InterviewBot
import tempfile
import time
import cv2
import numpy as np
import threading
import queue
import sounddevice as sd
import wave
import json
from datetime import datetime

# Initialize components
resume_parser = ResumeParser()
facial_analyzer = FacialEmotionAnalyzer() if FACIAL_EMOTION_AVAILABLE else None
voice_analyzer = VoiceAnalyzer()
speech_to_text = SpeechToText()
content_matcher = ContentMatcher()
interview_bot = InterviewBot()

# Global variables for state management
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = []
if 'skills' not in st.session_state:
    st.session_state.skills = []

def save_uploaded_file(uploaded_file):
    """Save uploaded file to temporary directory."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return tmp_file.name

def process_frame(frame, emotion_queue):
    """Process a single frame for emotion analysis."""
    try:
        if facial_analyzer:
            analysis = facial_analyzer.analyze_frame(frame)
            # Ensure the analysis has the required keys
            if 'dominant_emotion' not in analysis:
                analysis['dominant_emotion'] = 'neutral'
            if 'emotions' not in analysis:
                analysis['emotions'] = {}
            emotion_queue.put(analysis)
        else:
            emotion_queue.put({'dominant_emotion': 'unavailable', 'emotions': {}})
    except Exception as e:
        print(f"Error processing frame: {str(e)}")
        # Put a default emotion result even when there's an error
        emotion_queue.put({'dominant_emotion': 'error', 'emotions': {}})

def record_audio(duration, sample_rate=44100):
    """Record audio for a specified duration."""
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    sd.wait()
    return recording

def save_audio(recording, sample_rate=44100):
    """Save recorded audio to a temporary WAV file."""
    try:
        # Create a temporary file with explicit close to avoid Windows file locking
        import uuid
        temp_filename = f"temp_audio_{uuid.uuid4().hex[:8]}.wav"
        temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
        
        # Ensure recording is not empty and has valid data
        if len(recording) == 0:
            print("Warning: Empty recording")
            return None
            
        # Normalize audio data
        audio_data = np.array(recording).flatten()
        audio_data = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)
        
        # Save with explicit file handling
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())
        
        # Verify file was created
        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 44:  # More than just header
            return temp_path
        else:
            print(f"Error: Audio file not created properly: {temp_path}")
            return None
            
    except Exception as e:
        print(f"Error saving audio: {str(e)}")
        return None

def analyze_response(audio_path, video_frames, question, skills):
    """Analyze the user's response comprehensively."""
    # Initialize default results
    transcription = {'text': '', 'segments': [], 'language': 'es'}
    voice_analysis = {}
    
    # Check if audio file exists and is valid
    if audio_path and os.path.exists(audio_path):
        try:
            # Transcribe speech
            transcription = speech_to_text.transcribe(audio_path)
            
            # Analyze voice characteristics
            voice_features = voice_analyzer.extract_features(audio_path)
            voice_analysis = voice_analyzer.analyze_voice_characteristics(voice_features)
        except Exception as e:
            print(f"Error in audio analysis: {str(e)}")
            transcription = {'text': 'Error processing audio', 'segments': [], 'language': 'en'}
            voice_analysis = {'error': 'Audio analysis failed'}
    else:
        print(f"Audio file not available: {audio_path}")
        transcription = {'text': 'Audio recording failed', 'segments': [], 'language': 'en'}
        voice_analysis = {'error': 'No audio file'}
    
    # Analyze facial emotions
    if facial_analyzer and video_frames:
        try:
            emotion_analysis = facial_analyzer.analyze_frames(video_frames)
            # Ensure the analysis has the required keys
            if not isinstance(emotion_analysis, dict):
                emotion_analysis = {'dominant_emotion': 'error', 'emotions': {}}
            if 'dominant_emotion' not in emotion_analysis:
                emotion_analysis['dominant_emotion'] = 'neutral'
            if 'emotions' not in emotion_analysis:
                emotion_analysis['emotions'] = {}
        except Exception as e:
            print(f"Error in emotion analysis: {str(e)}")
            emotion_analysis = {'dominant_emotion': 'error', 'emotions': {}}
    else:
        emotion_analysis = {'dominant_emotion': 'unavailable', 'emotions': {}}
    
    # Match content with resume
    content_analysis = content_matcher.analyze_content_match(skills, transcription['text'])
    
    # Evaluate answer
    answer_evaluation = interview_bot.evaluate_answer(question, transcription['text'], skills)
    
    return {
        'transcription': transcription['text'],
        'voice_analysis': voice_analysis,
        'emotion_analysis': emotion_analysis,
        'content_analysis': content_analysis,
        'answer_evaluation': answer_evaluation,
        'timestamp': datetime.now().isoformat()
    }

def main():
    st.title("Sistema de analisis de entrevistas")
    
    # Sidebar for resume upload
    st.sidebar.header("Subir CV")
    resume_file = st.sidebar.file_uploader("Subir(PDF)", type=['pdf'])
    
    if resume_file:
        # Process resume
        with st.spinner("Analizando CV..."):
            resume_path = save_uploaded_file(resume_file)
            resume_analysis = resume_parser.analyze_resume(resume_path)
            if resume_analysis:
                st.session_state.skills = resume_analysis['skills']
                st.success("Analisis de CV completado!")
                st.sidebar.write("Extracted Skills:", resume_analysis['skills'])
                os.unlink(resume_path)
            else:
                st.error("Error al analizar CV. Revisar formato.")
                return
    
    # Main interview interface
    st.header("Entrevista en vivo")
    
    # Generate new question if none exists
    if not st.session_state.current_question and st.session_state.skills:
        st.session_state.current_question = interview_bot.generate_questions(
            st.session_state.skills, 
            num_questions=1
        )[0]
    
    # Display current question
    if st.session_state.current_question:
        st.write("### Pregunta actual")
        st.write(st.session_state.current_question['question'])
        
        # Start/Stop recording button
        if st.button("Comenzar grabacion"):
            st.session_state.is_recording = True
            
            # Create placeholders for live feedback
            emotion_placeholder = st.empty()
            voice_placeholder = st.empty()
            
            # Initialize video capture
            cap = cv2.VideoCapture(0)
            video_frames = []
            emotion_queue = queue.Queue()
            
            # Record for 30 seconds
            start_time = time.time()
            while time.time() - start_time < 30 and st.session_state.is_recording:
                ret, frame = cap.read()
                if ret:
                    # Process frame in a separate thread
                    threading.Thread(
                        target=process_frame,
                        args=(frame, emotion_queue)
                    ).start()
                    
                    video_frames.append(frame)
                    
                    # Display live emotion analysis
                    if not emotion_queue.empty():
                        emotion = emotion_queue.get()
                        # Safely access dominant_emotion with a fallback
                        dominant_emotion = emotion.get('dominant_emotion', 'unknown')
                        emotion_placeholder.write(f"Emocion Actual: {dominant_emotion}")
            
            cap.release()
            
            # Record audio
            audio_data = record_audio(30)
            audio_path = save_audio(audio_data)
            
            # Analyze response
            with st.spinner("Analizando tu respuesta..."):
                analysis = analyze_response(
                    audio_path,
                    video_frames,
                    st.session_state.current_question,
                    st.session_state.skills
                )
                
                st.session_state.analysis_results.append(analysis)
                
                # Display analysis results
                st.write("### Resultado del analisis")

                st.write("#### Transcripcion")
                print(f"🟡 Texto transcrito: '{analysis['transcription']}'")
                if not analysis['transcription'].strip():
                    st.warning("⚠️ No se obtuvo ninguna transcripción del audio.")
                
                st.write("#### Analisis de voz")
                st.write(analysis['voice_analysis'])
                
                st.write("#### Analisis de emociones")
                st.write(analysis['emotion_analysis'])
                
                st.write("#### Contenido similar")
                st.write(analysis['content_analysis'])
                
                st.write("#### Evaluacion de la respuesta")
                st.write(analysis['answer_evaluation'])
            
            # Clean up
            os.unlink(audio_path)
            st.session_state.is_recording = False
            
            # Generate next question
            st.session_state.current_question = interview_bot.generate_questions(
                st.session_state.skills,
                num_questions=1
            )[0]
    
    # Display interview history
    if st.session_state.analysis_results:
        st.header("Historial de entrevista")
        for i, result in enumerate(st.session_state.analysis_results):
            with st.expander(f"Response {i+1}"):
                st.write("Pregunta:", st.session_state.current_question['question'])
                st.write("Transcripcion:", result['transcription'])
                st.write("Evaluaacion:", result['answer_evaluation'])

if __name__ == "__main__":
    main() 