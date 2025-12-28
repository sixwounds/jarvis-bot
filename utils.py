import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def voice_to_text(file_path):
    with open(file_path, "rb") as audio:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-transcribe",
            file=audio,
            language="ru"
        )
    return transcript.text
