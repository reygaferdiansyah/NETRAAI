import streamlit as st
import requests
import base64
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
import os
import re

# load_dotenv()

# Credentials
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
SPEECH_KEY = os.getenv('SPEECH_KEY')
SERVICE_REGION = os.getenv('SERVICE_REGION')


# SERVICE_REGION = "southeastasia"
print(f'SPEECH_KEY 2: {SPEECH_KEY}')
print(f'SERVICE_REGION 2: {SERVICE_REGION}')

# Function to perform OCR using OpenAI (Note: OpenAI does not provide direct OCR service)
def ocr_image(image_content):
    image_data = base64.b64encode(image_content).decode('utf-8')

    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_API_KEY,
    }

    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "text": "Kamu adalah seorang guru dengan murid yang memiliki keterbatasan penglihatan (tuna netra). / Oleh karena itu, kamu harus menjelaskan teks dalam bentuk narasi./ Bantu mereka untuk bacakan dan jelaskan file yang dikirim kepada anda.",
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.5,
        "top_p": 0.95,
        "max_tokens": 800
    }

    try:
        response = requests.post(
            f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/gpt-4o/chat/completions?api-version=2024-02-15-preview",
            headers=headers, json=payload)
        response.raise_for_status()

    except requests.RequestException as e:
        raise SystemExit(f"Failed to make the request. Error: {e}")

    res = response.json()
    ocr_text = res['choices'][0]['message']['content']

    return ocr_text


# Function to clean and format text
def clean_text(text):
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Remove backslashes
    text = text.replace('\\', '')
    # Ensure sentences are well-separated
    text = re.sub(r'(?<!\.)\n(?!\.)', '. ', text)
    # Add a period at the end if not present
    if text and text[-1] not in {'.', '!', '?'}:
        text += '.'
    return text


# Function to convert text to speech using Azure Speech SDK
def text_to_speech(content):
    import azure.cognitiveservices.speech as speechsdk

    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(filename="output_audio.wav")  # Save audio to file

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = speech_synthesizer.speak_text_async(content).get()

    return "output_audio.wav"


# Function to convert PDF to images
def pdf_to_images(pdf_content):
    pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
    images = []
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        images.append(img_byte_arr.getvalue())
    return images


# Streamlit app
def main():
    st.title("NETRA AI")

    # Centering the main content
    st.header("Ubah Materi Teks dan Gambar Menjadi Audio")
    uploaded_file = st.file_uploader("Pilih file PDF atau Gambar", type=['pdf', 'jpg', 'jpeg', 'png'])

    if uploaded_file is not None:
        file_content = uploaded_file.read()
        file_type = uploaded_file.type

        if file_type.startswith('image/'):
            # Perform OCR on image
            ocr_result = ocr_image(file_content)

            # Clean and format OCR result
            clean_ocr_result = clean_text(ocr_result)

            # Convert OCR result to speech
            audio_file = text_to_speech(clean_ocr_result)
            st.audio(audio_file, format='audio/wav')

        elif file_type == 'application/pdf':
            # Process PDF pages to images and perform OCR on each page
            images = pdf_to_images(file_content)
            full_ocr_result = ""
            for image in images:
                ocr_result = ocr_image(image)
                full_ocr_result += ocr_result + "\n"

            # Clean and format full OCR result
            clean_full_ocr_result = clean_text(full_ocr_result)

            # Convert full OCR result to speech
            audio_file = text_to_speech(clean_full_ocr_result)
            st.audio(audio_file, format='audio/wav')

        else:
            st.warning("Format file tidak didukung. Harap unggah PDF atau gambar.")

    st.markdown("<p style='text-align: center;'>Powered by OpenAI and Azure Speech SDK</p>", unsafe_allow_html=True)


if __name__ == '__main__':
    main()
