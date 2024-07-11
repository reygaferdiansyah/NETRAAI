import os
import base64
import streamlit as st
from dotenv import load_dotenv
import scripts.aiml as ai
from audio_recorder_streamlit import audio_recorder  

load_dotenv()

st.title('NETRA AI')
st.header('Latihan Soal Essay dan Pilihan Ganda')
# 1. Guru upload gambar/pdf
uploaded_file = st.file_uploader("Upload a file (image or PDF)")
if uploaded_file is not None:
    temp_location = f"temp/document-{os.path.splitext(uploaded_file.name)[0]}.pdf"
    with open(temp_location, 'wb') as f:
        f.write(uploaded_file.getvalue())
    st.session_state['document_path'] = temp_location

# 2. Convert to Text
document_path = st.session_state.get('document_path')
if document_path:
    encoded_image = base64.b64encode(open(document_path, 'rb').read()).decode('ascii')
    question = ai.explain_image(encoded_image=encoded_image)
    st.session_state['question'] = question

# Tampilkan pertanyaan
question = st.session_state.get('question')
st.divider()
st.header('Pertanyaan:')
st.text(question if question else "Belum ada pertanyaan diproses.")

# 3. Convert to Speech and Display Audio
audio_path = None
if question:
    audio_path = document_path.replace('document', 'audio') + '.wav'
    if not os.path.exists(audio_path):
        ai.tts(question, audio_path=audio_path)
    st.audio(audio_path, format="audio/wav", start_time=0)

st.text(f'audio_path: {audio_path}')

# 4. Record jawaban + 5. STT
recorder_path = st.session_state.get('recorder_path')
if document_path:
    recorder_path = document_path.replace('document', 'recorder') + '.wav'

audio_bytes = audio_recorder("Click to record", "Click to stop recording")

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")
    with open(recorder_path, 'wb') as f:
        f.write(audio_bytes)
    answer = ai.stt(recorder_path)
    st.session_state['answer'] = answer

st.text(f'Your Answer: {st.session_state.get("answer", "Belum ada jawaban")}')

# 6. Grade
st.divider()
st.header('Grading')
submit = st.button('Submit', disabled=st.session_state.get('answer') is None)
if submit:
    if document_path and recorder_path and os.path.exists(recorder_path):
        is_correct, explanation = ai.grade_choices(question, st.session_state['answer'])

        st.session_state['is_correct'] = is_correct
        st.session_state['explanation'] = explanation

        # Tambahkan TTS untuk hasil grading dan penjelasan
        grade_audio_path = document_path.replace('document', 'grade') + '.wav'
        grade_text = f'Jawaban kamu: {is_correct}. Penjelasan: {explanation}'
        ai.tts(grade_text, audio_path=grade_audio_path)
        st.session_state['grade_audio_path'] = grade_audio_path

is_correct = st.session_state.get('is_correct', None)
explanation = st.session_state.get('explanation', None)
grade_audio_path = st.session_state.get('grade_audio_path', None)

st.markdown(f'Jawaban kamu: {is_correct}')
st.markdown(f'Penjelasan: {explanation}')

if grade_audio_path:
    st.audio(grade_audio_path, format="audio/wav", start_time=0)
