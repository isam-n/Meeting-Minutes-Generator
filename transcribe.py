import speech_recognition as sr

# Define your audio path
audio_path = "converted_audio.wav"

# Initialize recognizer
recognizer = sr.Recognizer()

# Prepare final transcript
full_transcript = ""

# Open the audio file
with sr.AudioFile(audio_path) as source:
    # (Assuming your version of sr.AudioFile exposes DURATION—if not, you can
    # use the wave module to get total length.)
    duration = int(source.DURATION)  
    offset = 0
    chunk_index = 1

    while offset < duration:
        # Record up to 60 seconds from the current file position
        audio_data = recognizer.record(source, duration=60)

        try:
            # Recognize the chunk
            text = recognizer.recognize_google(audio_data)
            chunk_text = text

        except sr.UnknownValueError:
            chunk_text = "[Unintelligible segment]"
        except sr.RequestError as e:
            chunk_text = f"[API error: {e}]"
            # Print and add to full transcript, then break out
            print(f"Chunk {chunk_index} ({offset}-{min(offset+60, duration)}s): {chunk_text}")
            full_transcript += chunk_text + " "
            break

        # Print this chunk’s result
        print(f"Chunk {chunk_index} ({offset}-{min(offset+60, duration)}s): {chunk_text}")

        # Append to the running full transcript
        full_transcript += chunk_text + " "

        # Advance
        offset += 60
        chunk_index += 1

# Print the full transcript at the end
print("\n===== FULL TRANSCRIPT =====")
print(full_transcript)

# Save the transcript to a text file
with open("transcript.txt", "w", encoding="utf-8") as f:
    f.write(full_transcript)
