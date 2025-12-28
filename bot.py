import os
from datetime import datetime
from threading import Thread
from flask import Flask
from telebot import TeleBot, types
from dotenv import load_dotenv
from nlp_providers import GPTProvider, GeminiProvider, GigaChatProvider
from db import get_dialog, add_message, reset_dialog, count_today_messages

load_dotenv()

bot = TeleBot(os.getenv("TELEGRAM_TOKEN"))

user_models = {}
ADMIN_IDS = [832410474]   # ← ТВОЙ ID, безлимит
DAILY_LIMIT = 40

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
    bot.send_message(message.chat.id, "Привет! Я Джарвис. Напиши /model чтобы выбрать нейросеть.")


@bot.message_handler(commands=["reset"])
def reset_memory(message):
    reset_dialog(message.from_user.id)
    add_message(message.from_user.id, "system", system_prompt())
    bot.send_message(message.chat.id, "Память очищена.")


@bot.message_handler(commands=["model"])
def choose_model(message):
    kb = types.InlineKeyboardMarkup()
    for m in providers:
        kb.add(types.InlineKeyboardButton(text=m.upper(), callback_data=m))
    bot.send_message(message.chat.id, "Выбери модель:", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_models[call.from_user.id] = call.data
    bot.answer_callback_query(call.id, f"Активна модель: {call.data.upper()}")


@bot.message_handler(func=lambda msg: True)
def chat(message):
    uid = message.from_user.id

    if uid not in ADMIN_IDS and count_today_messages(uid) >= DAILY_LIMIT:
        bot.send_message(message.chat.id, "🚫 Лимит 40 сообщений в сутки исчерпан.")
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
