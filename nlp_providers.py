import os
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
import google.generativeai as genai
from gigachat import GigaChat

SYSTEM_PROMPT = (
    "Тебя зовут Джарвис. Ты живой, уверенный и дружелюбный ассистент.\n"
    "Никогда не называй себя нейросетью, ИИ, моделью, GPT, Gemini или GigaChat."
)


class GPTProvider:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate(self, messages):
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        r = self.client.chat.completions.create(model="gpt-4o-mini", messages=msgs)
        return r.choices[0].message.content


class GeminiProvider:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("models/gemini-flash-latest")

    def generate(self, messages):
        text = SYSTEM_PROMPT + "\n"
        for m in messages:
            text += f"{m['role']}: {m['content']}\n"
        return self.model.generate_content(text).text


class GigaChatProvider:
    def __init__(self):
        self.client = GigaChat(credentials=os.getenv("GIGACHAT_AUTH"), verify_ssl_certs=False)

    def generate(self, messages):
        text = (
            "Ты Джарвис. Ты живой ассистент и никогда не раскрываешь технические детали.\n\n"
        )
        for m in messages:
            role = "Пользователь" if m["role"] == "user" else "Джарвис"
            text += f"{role}: {m['content']}\n"
        r = self.client.chat(text)
        return r.choices[0].message.content
