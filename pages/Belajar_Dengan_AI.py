import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
from audio_recorder_streamlit import audio_recorder
import time
import pygame

load_dotenv('./.env', override=True)

# Konfigurasi Azure Cognitive Services
SPEECH_KEY = os.getenv('SPEECH_KEY')
SERVICE_REGION = os.getenv('SERVICE_REGION')

# Konfigurasi Azure OpenAI
endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
api_key = os.environ["AZURE_OPENAI_API_KEY"]
deployment = "gpt-35-turbo"

# Inisialisasi Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version="2024-02-01",
)

# Inisialisasi pygame untuk pemutaran audio
pygame.mixer.init()

# Function to perform Speech-to-Text (STT)
def speech_to_text(file_path):
    try:
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
        source_language_config = speechsdk.languageconfig.SourceLanguageConfig("id-ID")
        audio_config = speechsdk.audio.AudioConfig(filename=file_path)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            source_language_config=source_language_config,
            audio_config=audio_config
        )
        
        result = speech_recognizer.recognize_once()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            return "Maaf, saya tidak bisa menangkap suara Anda."
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            return f"Pencarian Dibatalkan: {cancellation_details.reason}"
    except Exception as e:
        return f"An error occurred: {e}"

# Fungsi untuk melakukan Text-to-Speech (TTS)
def text_to_speech(text):
    try:
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
        # Using default speaker might cause issues, try alternative configuration
        audio_config = speechsdk.audio.AudioOutputConfig(filename="output.wav")

        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        synthesizer.speak_text_async(text).get()

        # Play the audio file (alternative method)
        pygame.mixer.music.load("output.wav")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():  # Wait for the audio to finish playing
            continue
    except Exception as e:
        st.error(f"Error in TTS: {e}")

# Function for interacting with the OpenAI Chatbot
def get_chatbot_response(user_input):
    user_input = user_input.lower().replace("/", " ").replace("\n", " ").strip()
    if "(id)" not in user_input:
        user_input += " (id)"
    
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": "Anda adalah asisten yang membantu memberikan jawaban dari semua pertanyaan pembelajaran dengan lengkap dan jelas.\n Kamu juga bisa memberikan penjelasan lengkap dengan banyak bidang materi.\n Yaitu materi Bahasa Indonesia, Matematika, Sejarah, Bahasa Inggris, Dan Musik"},
            {"role": "user", "content": user_input}
        ],
    )
    
    return response.choices[0].message.content

# Streamlit UI
st.title("NETRA AI")
st.header("Belajar Interaktif dengan AI")

st.header('Record Conversation')
audio_bytes = audio_recorder("Click to record", "Click to stop recording")
transcription = st.session_state.get('transcription', "")

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")

transcript = st.button('Transcript', type='primary')

if transcript:
    # Generate a new recorder_path if not already defined
    if 'recorder_path' not in st.session_state:
        st.session_state['recorder_path'] = f'outputs/recording/{time.strftime("%Y%m%d-%H%M%S")}.wav'

    # Write audio bytes to recorder_path
    with open(st.session_state['recorder_path'], 'wb+') as f:
        f.write(audio_bytes)

    # Perform speech to text conversion (example placeholder)
    transcription = speech_to_text(st.session_state['recorder_path'])

    # Store transcription in session state
    st.session_state['transcription'] = transcription

# Display transcription
st.text(f'Transcription: {transcription}')

# Use transcription as user input
user_input = transcription

if user_input:
    bot_response = get_chatbot_response(user_input)
    st.write("Chatbot:", bot_response)
    text_to_speech(bot_response)
