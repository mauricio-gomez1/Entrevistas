import streamlit as st
import os
from resume_parser import ResumeParser
from facial_emotion import FacialEmotionAnalyzer
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
facial_analyzer = FacialEmotionAnalyzer()
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
        analysis = facial_analyzer.analyze_frame(frame)
        emotion_queue.put(analysis)
    except Exception as e:
        print(f"Error processing frame: {str(e)}")

def record_audio(duration, sample_rate=44100):
    """Record audio for a specified duration."""
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    sd.wait()
    return recording

def save_audio(recording, sample_rate=44100):
    """Save recorded audio to a temporary WAV file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
        with wave.open(tmp_file.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes((recording * 32767).astype(np.int16).tobytes())
        return tmp_file.name

def analyze_response(audio_path, video_frames, question, skills):
    """Analyze the user's response comprehensively."""
    # Transcribe speech
    transcription = speech_to_text.transcribe(audio_path)
    
    # Analyze voice characteristics
    voice_features = voice_analyzer.extract_features(audio_path)
    voice_analysis = voice_analyzer.analyze_voice_characteristics(voice_features)
    
    # Analyze facial emotions
    emotion_analysis = facial_analyzer.analyze_frames(video_frames)
    
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
    st.title("Live Interview Analysis System")
    
    # Sidebar for resume upload
    st.sidebar.header("Upload Resume")
    resume_file = st.sidebar.file_uploader("Upload Resume (PDF)", type=['pdf'])
    
    if resume_file:
        # Process resume
        with st.spinner("Analyzing resume..."):
            resume_path = save_uploaded_file(resume_file)
            resume_analysis = resume_parser.analyze_resume(resume_path)
            if resume_analysis:
                st.session_state.skills = resume_analysis['skills']
                st.success("Resume analysis complete!")
                st.sidebar.write("Extracted Skills:", resume_analysis['skills'])
                os.unlink(resume_path)
            else:
                st.error("Failed to analyze resume. Please check the file format.")
                return
    
    # Main interview interface
    st.header("Live Interview")
    
    # Generate new question if none exists
    if not st.session_state.current_question and st.session_state.skills:
        st.session_state.current_question = interview_bot.generate_questions(
            st.session_state.skills, 
            num_questions=1
        )[0]
    
    # Display current question
    if st.session_state.current_question:
        st.write("### Current Question")
        st.write(st.session_state.current_question['question'])
        
        # Start/Stop recording button
        if st.button("Start Recording"):
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
                        emotion_placeholder.write(f"Current Emotion: {emotion['dominant_emotion']}")
            
            cap.release()
            
            # Record audio
            audio_data = record_audio(30)
            audio_path = save_audio(audio_data)
            
            # Analyze response
            with st.spinner("Analyzing your response..."):
                analysis = analyze_response(
                    audio_path,
                    video_frames,
                    st.session_state.current_question,
                    st.session_state.skills
                )
                
                st.session_state.analysis_results.append(analysis)
                
                # Display analysis results
                st.write("### Analysis Results")
                st.write("#### Speech Transcription")
                st.write(analysis['transcription'])
                
                st.write("#### Voice Analysis")
                st.write(analysis['voice_analysis'])
                
                st.write("#### Emotion Analysis")
                st.write(analysis['emotion_analysis'])
                
                st.write("#### Content Matching")
                st.write(analysis['content_analysis'])
                
                st.write("#### Answer Evaluation")
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
        st.header("Interview History")
        for i, result in enumerate(st.session_state.analysis_results):
            with st.expander(f"Response {i+1}"):
                st.write("Question:", st.session_state.current_question['question'])
                st.write("Transcription:", result['transcription'])
                st.write("Evaluation:", result['answer_evaluation'])

if __name__ == "__main__":
    main() 