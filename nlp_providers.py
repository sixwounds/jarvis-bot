import os
import time
import requests


class GigaChatProvider:
    def __init__(self):
        self.auth_key = os.getenv("GIGACHAT_AUTH_KEY")
        self.token = None
        self.token_expire = 0

    def _get_token(self):
        if self.token and time.time() < self.token_expire:
            return self.token

        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            "Authorization": f"Basic {self.auth_key}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        data = {"scope": "GIGACHAT_API_PERS"}

        r = requests.post(url, headers=headers, data=data, verify=False)

        if r.status_code != 200:
            raise Exception(f"GigaChat OAuth error {r.status_code}: {r.text}")

        j = r.json()
        self.token = j["access_token"]
        self.token_expire = time.time() + int(j["expires_in"]) - 60
        return self.token

    def ask(self, dialog):
        token = self._get_token()

        payload = {
            "model": "GigaChat",
            "messages": dialog,
            "temperature": 0.7,
            "top_p": 0.9
        }

        r = requests.post(
            "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json=payload,
            verify=False
        )

        if r.status_code != 200:
            raise Exception(f"GigaChat API error {r.status_code}: {r.text}")

        return r.json()["choices"][0]["message"]["content"]
