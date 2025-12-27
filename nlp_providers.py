import os
import uuid
import requests
from dotenv import load_dotenv
from openai import OpenAI
import google.genai as genai

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class GPTProvider:
    def generate(self, messages):
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )
        return resp.choices[0].message.content


class GeminiProvider:
    def generate(self, messages):
        prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)

        resp = gemini_client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=prompt
        )
        return resp.text.strip()


class GigaChatProvider:
    def __init__(self):
        self.auth_key = os.getenv("GIGACHAT_AUTH_KEY")
        self.token = None

    def _get_token(self):
        headers = {
            "Authorization": f"Basic {self.auth_key}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded"
        }

        r = requests.post(
            "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
            headers=headers,
            data={"scope": "GIGACHAT_API_PERS"},
            verify=False,
            timeout=20
        )

        if r.status_code != 200:
            raise Exception(f"OAuth error: {r.status_code} {r.text}")

        self.token = r.json()["access_token"]

    def _headers(self):
        if not self.token:
            self._get_token()
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def generate(self, messages):
        headers = self._headers()
        prompt = "\n".join(m["content"] for m in messages if m["role"] != "system")

        payload = {
            "model": "GigaChat",
            "messages": [{"role": "user", "content": prompt}]
        }

        r = requests.post(
            "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
            headers=headers,
            json=payload,
            verify=False,
            timeout=30
        )

        if r.status_code != 200:
            raise Exception(f"GigaChat error: {r.status_code} {r.text}")

        return r.json()["choices"][0]["message"]["content"]

    def draw(self, prompt):
        headers = self._headers()

        payload = {
            "model": "GigaChat:Kandinsky",
            "prompt": prompt,
            "n": 1
        }

        r = requests.post(
            "https://gigachat.devices.sberbank.ru/api/v1/images/generations",
            headers=headers,
            json=payload,
            verify=False,
            timeout=60
        )

        if r.status_code != 200:
            raise Exception(f"Kandinsky error: {r.status_code} {r.text}")

        return r.json()["data"][0]["url"]
