from flask import Flask, render_template, request, send_file
import os
import datetime
import markdown   # pip install markdown

from pydub import AudioSegment
import speech_recognition as sr

from summarizer import generate_minutes

# PDF generation imports
from xhtml2pdf import pisa
import io

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def index():
    # Defaults so the form “remembers” your inputs
    date_str     = datetime.date.today().isoformat()
    attendees    = ""
    topic        = ""
    transcript   = None
    chunk_texts  = []
    summary_html = None

    if request.method == "POST":
        file      = request.files.get("audio_file")
        date_str  = request.form.get("date", date_str)
        attendees = request.form.get("attendees", "").strip()
        topic     = request.form.get("topic", "").strip()

        # accept wav, m4a, mp4
        if file and file.filename.lower().endswith((".wav", ".m4a", ".mp4")):
            # --- Save upload ---
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(input_path)

            # --- Convert to .wav if needed ---
            ext = os.path.splitext(input_path)[1].lower()
            if ext in (".m4a", ".mp4"):
                wav_path = os.path.join(app.config['UPLOAD_FOLDER'], "converted_audio.wav")
                # pydub will use ffmpeg under the hood to extract audio from m4a or mp4
                audio = AudioSegment.from_file(input_path, format=ext[1:])
                audio.export(wav_path, format="wav")
            else:
                # already .wav
                wav_path = input_path

            # --- Chunked transcription ---
            recognizer      = sr.Recognizer()
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

                    print(f"Chunk {idx} ({offset}-{min(offset+60, duration)}s): {text}")
                    full_transcript += text + " "
                    chunk_texts.append(text)

                    offset += 60
                    idx    += 1

            transcript = full_transcript

            # --- Generate & render summary ---
            summary_md   = generate_minutes(transcript, date_str, attendees, topic)
            summary_html = markdown.markdown(
                summary_md,
                extensions=["extra", "sane_lists"]
            )

    return render_template(
        "index.html",
        date=date_str,
        attendees=attendees,
        topic=topic,
        transcript=transcript,
        chunk_texts=chunk_texts,
        summary_html=summary_html
    )

@app.route("/download", methods=["POST"])
def download_pdf():
    html_body = request.form.get("summary_html", "")
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
      {html_body}
    </body></html>
    """
    pdf_buffer = io.BytesIO()
    status = pisa.CreatePDF(full_html, dest=pdf_buffer)
    if status.err:
        return "Error generating PDF", 500

    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name="meeting_minutes.pdf",
        mimetype="application/pdf"
    )

if __name__ == "__main__":
    app.run(debug=True)
