# summarizer.py
import os
from mistralai import Mistral

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
client = Mistral(api_key=MISTRAL_API_KEY)

def generate_minutes(transcript: str, date: str, attendees: str, topic: str) -> str:
    """
    Returns a meeting minutes summary in Markdown,
    with proper blank lines so that lists render as lists.
    """
    system_prompt = f"""
You are a meeting assistant.  You MUST output in Markdown, using **bold** for all headings exactly as shown.
Do NOT change the template or merge headings and content onto the same line, and keep these exact labels.

**Meeting Minutes Summary**

**Date:** {date}

**Attendees:** {attendees}

**Topic:** {topic}

________________________________________

**Key Discussion Points:**

1. **…**  
   - …  

________________________________________

**Decisions and Next Steps:**

- …  

________________________________________

**Action Items:**

- …  
"""

    user_prompt = f"""
Here is the transcript:

\"\"\"
{transcript}
\"\"\"

Replace every placeholder bullet under each section above with actual points drawn from the transcript,
preserving all headings, separators, blank lines, and your exact **Date**, **Attendees**, and **Topic**.
"""

    resp = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        stream=False
    )

    return resp.choices[0].message.content.strip()
