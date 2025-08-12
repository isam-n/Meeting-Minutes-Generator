from pydub import AudioSegment
import os

# Convert the uploaded .m4a file to .wav for transcription compatibility
input_path = "meeting.m4a"
output_path = "converted_audio.wav"

# Load and convert the file
audio = AudioSegment.from_file(input_path, format="m4a")
audio.export(output_path, format="wav")

output_path