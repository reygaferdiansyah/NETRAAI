import fitz  # PyMuPDF
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
import os
import time

# Masukkan key dan endpoint
subscription_key = os.getenv('SUBSCRIPTION_KEY')
endpoint = os.getenv('ENDPOINT')

# Autentikasi ke layanan
computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

# Fungsi untuk memproses gambar menggunakan OCR
def ocr_image(image_path):
    with open(image_path, "rb") as image_stream:
        ocr_result = computervision_client.read_in_stream(image_stream, raw=True)
    # Mendapatkan hasil OCR
    operation_location = ocr_result.headers["Operation-Location"]
    operation_id = operation_location.split("/")[-1]

    # Memeriksa status hasil OCR
    while True:
        result = computervision_client.get_read_result(operation_id)
        if result.status.lower() not in ['notstarted', 'running']:
            break
        time.sleep(1)

    # Ambil teks hasil OCR
    text = ""
    if result.status == 'succeeded':
        for page in result.analyze_result.read_results:
            for line in page.lines:
                text += line.text + "\n"
    return text

# Fungsi untuk mengonversi PDF menjadi gambar dan melakukan OCR
def process_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    all_text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        image_path = f"page_{page_num + 1}.png"
        pix.save(image_path)
        print(f"Processing page {page_num + 1}")
        page_text = ocr_image(image_path)
        all_text += page_text
        os.remove(image_path)  # Hapus gambar sementara
    return all_text

# Fungsi utama untuk memproses file
def process_file(file_path):
    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
        # Jika file adalah gambar
        return ocr_image(file_path)
    elif file_path.lower().endswith('.pdf'):
        # Jika file adalah PDF
        return process_pdf(file_path)
    else:
        print("Unsupported file format")
        return ""

# Path ke file gambar atau PDF
file_paths = [
    "./test1.png"
]

# Proses setiap file dalam daftar
for file_path in file_paths:
    print(f"Processing file: {file_path}")
    text = process_file(file_path)
    if text:
        output_path = file_path + ".txt"
        with open(output_path, "w", encoding='utf-8') as text_file:
            text_file.write(text)
        print(f"Output written to {output_path}")