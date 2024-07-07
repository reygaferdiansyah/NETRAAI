import os
import time

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import azure.cognitiveservices.speech as speechsdk


# Set environment variables directly (for testing purpose)
language_key = os.environ.get('LANGUAGE_KEY')
language_endpoint = os.environ.get('LANGUAGE_ENDPOINT')

speech_key = os.getenv('SPEECH_KEY')
service_region = os.getenv('SERVICE_REGION')
timestr = time.strftime("%Y%m%d-%H%M%S")
audio_path = f"./../Audio/outputs-speech-{timestr}.wav"
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

if not language_key or not language_endpoint:
    raise ValueError("Please set the LANGUAGE_KEY and LANGUAGE_ENDPOINT environment variables.")


# Fungsi untuk membaca isi file teks dan mengembalikannya sebagai string
def txt_to_string(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text

# Path ke file teks
file_path = "./test2.png.txt"

# Membaca isi file teks
text = txt_to_string(file_path)

# Authenticate the client using your key and endpoint
def authenticate_client():
    ta_credential = AzureKeyCredential(language_key)
    text_analytics_client = TextAnalyticsClient(
            endpoint=language_endpoint,
            credential=ta_credential)
    return text_analytics_client

client = authenticate_client()

# Example method for detecting the language of text
def language_detection(client, text):
    try:
        # Memanggil metode detect_language dengan teks sebagai list of documents
        response = client.detect_language(documents=[text], country_hint='us')[0]
        return response.primary_language.iso6391_name

    except Exception as err:
        print("Encountered exception. {}".format(err))
    return response.primary_language.iso6391_name
detected_language=language_detection(client,text)

# Choose voice based on detected language
voice_map = {
    'id': 'id-ID-GadisNeural',       # Bahasa Indonesia
    'en': 'en-US-GuyNeural',         # Bahasa Inggris (AS)
    'es': 'es-MX-JorgeNeural',       # Bahasa Spanyol (Meksiko)
    'fr': 'fr-FR-DeniseNeural',      # Bahasa Prancis (Prancis)
    'de': 'de-DE-ConradNeural',      # Bahasa Jerman (Jerman)
    'ar': 'ar-SA-HamedNeural',       # Bahasa Arab (Arab Saudi)
    'zh_chs': 'zh-CN-XiaoxiaoNeural',    # Bahasa Mandarin (China)
    'ja': 'ja-JP-NanamiNeural',      # Bahasa Jepang
    'pt': 'pt-BR-FranciscaNeural',   # Bahasa Portugis (Brasil)
    'ru': 'ru-RU-SvetlanaNeural',    # Bahasa Rusia
    'nl': 'nl-NL-ColetteNeural',     # Bahasa Belanda
    'ko': 'ko-KR-SunHiNeural',       # Bahasa Korea
    'tr': 'tr-TR-EmelNeural',        # Bahasa Turki
    'sv': 'sv-SE-HilleviNeural',     # Bahasa Swedia
    'pl': 'pl-PL-ZofiaNeural',       # Bahasa Polandia
    'cs': 'cs-CZ-VlastaNeural',      # Bahasa Ceska (Ceko)
    'hu': 'hu-HU-NoemiNeural',       # Bahasa Hungaria
    'ro': 'ro-RO-EmilNeural',        # Bahasa Rumania
    'sk': 'sk-SK-LukasNeural',       # Bahasa Slovak
    'bg': 'bg-BG-BorislavNeural',    # Bahasa Bulgaria
    'hr': 'hr-HR-GabrijelaNeural',   # Bahasa Kroasia
    'lv': 'lv-LV-NilsNeural',        # Bahasa Latvia
    'it':'it-IT-ElsaNeural',         # Bahasa Italia
    'vi':'vi-VN-HoaiMyNeural'        # Bahsa Vietnam
            }
    # Add more languages and voices as needed

# Fallback to a default voice if language is not in the map
voice = voice_map.get(detected_language)
# Note: the voice setting will not overwrite the voice element in input SSML.
speech_config.speech_synthesis_voice_name = voice
audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_path)
# use the default speaker as audio output.
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
result = speech_synthesizer.speak_text_async(text).get()