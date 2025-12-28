import os
import time
from threading import Thread
from flask import Flask
from telebot import TeleBot, types
from dotenv import load_dotenv

from nlp_providers import GPTProvider, GeminiProvider, GigaChatProvider
from db import get_dialog, add_message, reset_dialog, count_today_messages
from utils import voice_to_text

load_dotenv()

bot = TeleBot(os.getenv("TELEGRAM_TOKEN"))

ADMIN_IDS = [832410474]
DAILY_LIMIT = 40
MAX_HISTORY = 12

user_models = {}

providers = {
    "gpt": GPTProvider(),
    "gemini": GeminiProvider(),
    "gigachat": GigaChatProvider()
}

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
        "👋 Привет! Я Джарвис.\n\n"
        "/model — выбрать нейросеть\n"
        "/draw <описание> — нарисовать\n"
        "/stats — статистика\n"
        "/limits — правила\n"
        "/reset — очистить память"
    )


@bot.message_handler(commands=["stats"])
def stats(message):
    uid = message.from_user.id
    used = count_today_messages(uid)
    if uid in ADMIN_IDS:
        bot.send_message(message.chat.id, f"Ты администратор. Использовано сегодня: {used}")
    else:
        bot.send_message(message.chat.id, f"Использовано: {used}/{DAILY_LIMIT}")


@bot.message_handler(commands=["limits"])
def limits(message):
    bot.send_message(message.chat.id,
        f"Лимит: {DAILY_LIMIT} сообщений в сутки\nАдминистратор — безлимит"
    )


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


@bot.message_handler(content_types=["voice"])
def voice_handler(message):
    file_info = bot.get_file(message.voice.file_id)
    downloaded = bot.download_file(file_info.file_path)

    path = f"voice_{message.from_user.id}.ogg"
    with open(path, "wb") as f:
        f.write(downloaded)

    try:
        text = voice_to_text(path)
        bot.send_message(message.chat.id, f"🎙 Ты сказал:\n{text}")
        message.text = text
        chat(message)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка распознавания: {e}")



@bot.message_handler(func=lambda msg: True)
def chat(message):
    uid = message.from_user.id

    if uid not in ADMIN_IDS and count_today_messages(uid) >= DAILY_LIMIT:
        bot.send_message(message.chat.id, "🚫 Лимит сообщений исчерпан.")
        return

    user_models.setdefault(uid, "gpt")

    history = get_dialog(uid)
    if not history:
        add_message(uid, "system", system_prompt())

    add_message(uid, "user", message.text)
    history = get_dialog(uid)[-MAX_HISTORY:]

    try:
        answer = providers[user_models[uid]].generate(history)
    except Exception as e:
        answer = f"Ошибка: {e}"

    add_message(uid, "assistant", answer)
    bot.send_message(message.chat.id, answer)


def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


Thread(target=run_flask).start()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
