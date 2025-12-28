import os
import time
import requests
from datetime import datetime
from threading import Thread
from flask import Flask
from telebot import TeleBot, types
from dotenv import load_dotenv
from nlp_providers import GPTProvider, GeminiProvider, GigaChatProvider
from db import get_dialog, add_message, reset_dialog

load_dotenv()

bot = TeleBot(os.getenv("TELEGRAM_TOKEN"))

user_models = {}

providers = {
    "gpt": GPTProvider(),
    "gemini": GeminiProvider(),
    "gigachat": GigaChatProvider()
}

MAX_HISTORY = 12

app = Flask(__name__)

@app.route("/")
def index():
    return "Jarvis is alive"


def system_prompt():
    return "Тебя зовут Джарвис. Ты умный, харизматичный ассистент. Общайся уверенно и по делу."


@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    user_models[uid] = "gpt"
    reset_dialog(uid)
    add_message(uid, "system", system_prompt())
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я **Джарвис** — твой персональный AI.\n\n"
        "Команды:\n"
        "/model — выбрать нейросеть\n"
        "/draw <описание> — создать изображение\n"
        "/reset — очистить память",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["reset"])
def reset_memory(message):
    reset_dialog(message.from_user.id)
    add_message(message.from_user.id, "system", system_prompt())
    bot.send_message(message.chat.id, "🧠 Память очищена")


@bot.message_handler(commands=["model"])
def choose_model(message):
    kb = types.InlineKeyboardMarkup()
    for m in providers:
        kb.add(types.InlineKeyboardButton(text=m.upper(), callback_data=m))
    bot.send_message(message.chat.id, "Выбери нейросеть:", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_models[call.from_user.id] = call.data
    bot.answer_callback_query(call.id, f"Активна модель: {call.data.upper()}")


@bot.message_handler(commands=["draw"])
def draw(message):
    prompt = message.text.replace("/draw", "").strip()
    if not prompt:
        bot.send_message(message.chat.id, "Напиши описание после /draw")
        return

    bot.send_message(message.chat.id, "🎨 Рисую...")
    try:
        img_url = providers["gigachat"].draw(prompt)
        bot.send_photo(message.chat.id, img_url)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка генерации: {e}")


@bot.message_handler(func=lambda msg: True)
def chat(message):
    uid = message.from_user.id
    text = message.text.lower()

    if "какой сейчас год" in text:
        bot.send_message(message.chat.id, str(datetime.now().year))
        return

    user_models.setdefault(uid, "gpt")

    history = get_dialog(uid)
    if not history:
        add_message(uid, "system", system_prompt())
        history = get_dialog(uid)

    add_message(uid, "user", message.text)
    history = get_dialog(uid)[-MAX_HISTORY:]

    provider = providers[user_models[uid]]

    try:
        answer = provider.generate(history)
    except Exception as e:
        answer = f"Ошибка API: {e}"

    add_message(uid, "assistant", answer)
    bot.send_message(message.chat.id, answer)


def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


Thread(target=run_flask).start()
bot.polling()
