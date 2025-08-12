import streamlit as st
import os
import datetime
import io
import markdown
from pydub import AudioSegment
import speech_recognition as sr
from summarizer import generate_minutes  # Your existing function
from xhtml2pdf import pisa

# Ensure uploads folder exists
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

st.set_page_config(page_title="Meeting Minutes Generator", layout="wide")
st.title("📄 Meeting Minutes Generator")

# --- Form Inputs ---
with st.form("upload_form", clear_on_submit=False):
    audio_file = st.file_uploader("Audio/Video file (.wav, .m4a, .mp4)",
                                  type=["wav", "m4a", "mp4"])
    date_str = st.date_input("Date", datetime.date.today())
    topic = st.text_input("Topic", placeholder="E.g. AI Demos")
    attendees = st.text_input("Attendees (comma-separated)")
    submit_btn = st.form_submit_button("Upload & Generate")

transcript = None
chunk_texts = []
summary_html = None

if submit_btn and audio_file:
    file_path = os.path.join(UPLOAD_FOLDER, audio_file.name)
    with open(file_path, "wb") as f:
        f.write(audio_file.getbuffer())

    ext = os.path.splitext(file_path)[1].lower()
    if ext in (".m4a", ".mp4"):
        wav_path = os.path.join(UPLOAD_FOLDER, "converted_audio.wav")
        audio = AudioSegment.from_file(file_path, format=ext[1:])
        audio.export(wav_path, format="wav")
    else:
        wav_path = file_path

    recognizer = sr.Recognizer()
    full_transcript = ""

    with sr.AudioFile(wav_path) as source:
        duration, offset, idx = int(source.DURATION), 0, 1
        while offset < duration:
            chunk = recognizer.record(source, duration=60)
            try:
                text = recognizer.recognize_google(chunk)
            except sr.UnknownValueError:
                text = ""
            except sr.RequestError as e:
                text = f"[API error: {e}]"
                break

            full_transcript += text + " "
            chunk_texts.append(text)
            offset += 60
            idx += 1

    transcript = full_transcript
    summary_md = generate_minutes(transcript, date_str, attendees, topic)
    summary_html = markdown.markdown(summary_md, extensions=["extra", "sane_lists"])

if transcript:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Minute-by-minute Transcript")
        for c in chunk_texts:
            st.write(f"- {c}")

        st.subheader("Full Transcript")
        st.code(transcript, language="text")

    with col2:
        st.subheader("Meeting Minutes Summary")
        st.markdown(summary_html, unsafe_allow_html=True)

        # PDF Download
        def create_pdf(html_content):
            full_html = f"""
            <!DOCTYPE html><html><head>
              <meta charset="utf-8"><title>Meeting Minutes</title>
              <style>
                body {{ font-family: sans-serif; margin: 2em; }}
                h1,h2,h3 {{ margin-bottom: .5em; }}
                hr {{ border: none; border-top: 1px solid #ccc; margin: 1em 0; }}
                ul,ol {{ margin-left: 1.5em; }}
                strong {{ font-weight: bold; }}
              </style>
            </head><body>
              {html_content}
            </body></html>
            """
            pdf_buffer = io.BytesIO()
            pisa.CreatePDF(full_html, dest=pdf_buffer)
            pdf_buffer.seek(0)
            return pdf_buffer

        pdf_file = create_pdf(summary_html)
        st.download_button("📄 Download as PDF",
                           data=pdf_file,
                           file_name="meeting_minutes.pdf",
                           mime="application/pdf")
