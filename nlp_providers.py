import os
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
import google.generativeai as genai
from gigachat import GigaChat


SYSTEM_PROMPT = (
    "Тебя зовут Джарвис. Ты никогда не называешь себя нейросетью, ИИ, моделью, "
    "GPT, Gemini, GigaChat, продуктом какой-либо компании.\n"
    "Ты — единый харизматичный ассистент, говоришь на 'ты', общаешься живо и уверенно."
)


class GPTProvider:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate(self, messages):
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + messages[-10:]
        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=msgs
        )
        return resp.choices[0].message.content


class GeminiProvider:
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel("models/gemini-flash-latest")

    def generate(self, messages):
        chat = self.model.start_chat(history=[])
        prompt = SYSTEM_PROMPT + "\n\n"
        for m in messages[-10:]:
            prompt += f"{m['role']}: {m['content']}\n"
        return chat.send_message(prompt).text


class GigaChatProvider:
    def __init__(self):
        self.client = GigaChat(
            credentials=os.getenv("GIGACHAT_AUTH"),
            verify_ssl_certs=False
        )

    def generate(self, messages):
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + messages[-10:]
        resp = self.client.chat(msgs)
        return resp.choices[0].message.content
