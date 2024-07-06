import os
import json
import time
import base64
import requests

from openai import AzureOpenAI
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import azure.cognitiveservices.speech as speechsdk

from dotenv import load_dotenv

AZURE_OPENAI_API_KEY="6ec8053e11d34bb6acc03330388ba9db"
AZURE_OPENAI_ENDPOINT="https://talenta-ai-2024-batch2.openai.azure.com/"
LANGUAGE_KEY = "e9f4cdd908644112ad185b60e0591022"
LANGUAGE_ENDPOINT = "https://deteksibahasa.cognitiveservices.azure.com/"
# AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
# AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
# LANGUAGE_KEY = os.environ.get('LANGUAGE_KEY')
# LANGUAGE_ENDPOINT = os.environ.get('LANGUAGE_ENDPOINT')
SPEECH_KEY = "232d072838de4797908c738708459c41"
SERVICE_REGION = "southeastasia"


def explain_image(encoded_image):
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_API_KEY,
    }

    # Payload for the request
    payload = {
        "messages": [
            {
            "role": "system",
            "content": [
                {
                "type": "text",
                "text": "Kamu adalah seorang guru di sekolah luar biasa (SLB). Saat ini kamu sedang mengadakan ujian. Peserta didik memiliki keterbatasan penglihatan (tuna netra). Oleh karena itu, kamu harus menjelaskan soal ujian berikut ini dalam bentuk narasi.\n\nIngat, hanya sampaikan soal ujian nya saja, tidak perlu di jawab."
                }
            ]
            },
            {
            "role": "user",
            "content": [
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{encoded_image}"
                }
                }
            ]
            },
        ],
        "temperature": 0.5,
        "top_p": 0.95,
        "max_tokens": 800
    }

    # Send request
    try:
        print(f'Calling GPT...')
        GPT4V_ENDPOINT = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview"
        response = requests.post(GPT4V_ENDPOINT, headers=headers, json=payload)
        response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code

    except requests.RequestException as e:
        raise SystemExit(f"Failed to make the request. Error: {e}")

    print(f'Response: {response.text}')
    res = response.json()
    return res['choices'][0]['message']['content']

def tts(content, audio_path=None):
    if audio_path is None:
        timestr = time.strftime("%Y%m%d-%H%M%S")
        audio_path = f"outputs/outputs-speech-{timestr}.wav"
    
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)

    if not LANGUAGE_KEY or not LANGUAGE_ENDPOINT:
        raise ValueError("Please set the LANGUAGE_KEY and LANGUAGE_ENDPOINT environment variables.")

    # Authenticate the client using your key and endpoint
    def authenticate_client():
        ta_credential = AzureKeyCredential(LANGUAGE_KEY)
        text_analytics_client = TextAnalyticsClient(
                endpoint=LANGUAGE_ENDPOINT,
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
    detected_language = language_detection(client, content)

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
    result = speech_synthesizer.speak_text_async(content).get()

    return audio_path

def stt(audio_path):
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
    source_language_config = speechsdk.languageconfig.SourceLanguageConfig("id-ID")  
    audio_config = speechsdk.audio.AudioConfig(filename=audio_path)

    speech_recognizer = speechsdk.SpeechRecognizer(  
        speech_config=speech_config, 
        source_language_config=source_language_config, 
        audio_config=audio_config
    )

    result = speech_recognizer.recognize_once()
    return result.text

def grade_choices(question, answer):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "berikan_penilaian",
                "description": "Berika penilaian",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "benar_salah": {
                            "type": "boolean",
                            "description": "Apakah jawaban pengguna benar atau salah",
                        },
                        "penjelasan": {
                            "type": "string",
                            "description": "Jelaskan jawaban yang benar",
                        },
                    },
                    "required": ["benar_salah", "penjelasan"],
                },
            },
        }
    ]

    client = AzureOpenAI(
        api_version="2024-02-01",
    )
    completion = client.chat.completions.create(
        model="gpt-35-turbo" ,
        messages=[
            {
                "role": "system",
                "content": """Kamu adalah seorang guru yang saat ini sedang mengadakan ujian. Soal berupa pilihan ganda. 
    Berikut adalah solanya:""".strip(),
            },
            {
                "role": "system",
                "content": question.strip(),
            },
            {
                "role": "user",
                "content": answer.strip(),
            },
            {
                "role": "assistant",
                "content": """
    Berdasarkan jawaban pengguna di atas ini, berikan penilaian dalam format berikut:
    Jawaban: BENAR atau SALAH
    Penjelasan: Jelaskan jawaban yang benar""".strip()
            },
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "berikan_penilaian"}}
    )
        
    # print(completion.to_json())
    args = json.loads(completion.choices[0].message.tool_calls[0].function.arguments)
    is_correct = args['benar_salah']
    explanation = args['penjelasan']

    return is_correct, explanation


def grade_essay(question, answer):
    # TODO
    raise NotImplementedError

    tools = [
        {
            "type": "function",
            "function": {
                "name": "berikan_penilaian",
                "description": "Berika penilaian",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nilai": {
                            "type": "number",
                            "description": "Nilai dari 0-10",
                        },
                        "penjelasan": {
                            "type": "string",
                            "description": "Jelaskan jawaban yang benar",
                        },
                    },
                    "required": ["benar_salah", "penjelasan"],
                },
            },
        }
    ]

    client = AzureOpenAI(
        api_version="2024-02-01",
    )
    completion = client.chat.completions.create(
        model="gpt-35-turbo" ,
        messages=[
            {
                "role": "system",
                "content": """Kamu adalah seorang guru yang saat ini sedang mengadakan ujian. Soal berupa pilihan ganda. 
    Berikut adalah solanya:""".strip(),
            },
            {
                "role": "system",
                "content": question.strip(),
            },
            {
                "role": "user",
                "content": answer.strip(),
            },
            {
                "role": "assistant",
                "content": """
    Berdasarkan jawaban pengguna di atas ini, berikan penilaian dalam format berikut:
    Jawaban: BENAR atau SALAH
    Penjelasan: Jelaskan jawaban yang benar""".strip()
            },
        ],
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "berikan_penilaian"}}
    )
        
    # print(completion.to_json())
    args = json.loads(completion.choices[0].message.tool_calls[0].function.arguments)
    is_correct = args['benar_salah']
    explanation = args['penjelasan']

    return is_correct, explanation
