import os
from threading import Thread
from flask import Flask
from telebot import TeleBot, types
from dotenv import load_dotenv

from nlp_providers import GPTProvider, GeminiProvider, GigaChatProvider
from db import get_dialog, add_message, reset_dialog, get_today_count, inc_today_count, daily_reset_loop

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
    return (
        "Тебя зовут Джарвис.\n"
        "Ты харизматичный, дружелюбный, живой ассистент, который говорит на 'ты'.\n"
        "Ты никогда не называешь себя моделью, нейросетью, ИИ, GPT, GigaChat или Gemini.\n"
        "Ты — единый персонаж.\n"
        "Общайся свободно, уверенно, иногда шути, будь тёплым и разговорчивым.\n"
        "Помогай, советуй, поддерживай диалог как хороший знакомый."
    )


@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    user_models[uid] = "gpt"
    reset_dialog(uid)
    add_message(uid, "system", system_prompt())
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я Джарвис — твой персональный помощник.\n\n"
        "Можем просто поболтать или заняться делом.\n\n"
        "/model — выбрать нейросеть\n"
        "/stats — статистика\n"
        "/limits — правила\n"
        "/reset — очистить память"
    )


@bot.message_handler(commands=["stats"])
def stats(message):
    uid = message.from_user.id
    used = get_today_count(uid)
    if uid in ADMIN_IDS:
        bot.send_message(message.chat.id, f"Ты сегодня написал {used} сообщений. У тебя безлимит 😎")
    else:
        bot.send_message(message.chat.id, f"Сегодня ты использовал {used} из {DAILY_LIMIT} сообщений.")


@bot.message_handler(commands=["limits"])
def limits(message):
    bot.send_message(
        message.chat.id,
        f"📜 Правила простые:\n"
        f"• {DAILY_LIMIT} сообщений в сутки\n"
        "• лимиты обнуляются каждый день в 00:00\n"
        "• у администратора — безлимит"
    )


@bot.message_handler(commands=["reset"])
def reset_memory(message):
    reset_dialog(message.from_user.id)
    add_message(message.from_user.id, "system", system_prompt())
    bot.send_message(message.chat.id, "🧠 Всё, начинаем с чистого листа.")


@bot.message_handler(commands=["model"])
def choose_model(message):
    kb = types.InlineKeyboardMarkup()
    for m in providers:
        kb.add(types.InlineKeyboardButton(text=m.upper(), callback_data=m))
    bot.send_message(message.chat.id, "Выбери, с кем сегодня болтаем:", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_models[call.from_user.id] = call.data
    bot.answer_callback_query(call.id, f"Теперь с тобой общается: {call.data.upper()}")


@bot.message_handler(func=lambda msg: True)
def chat(message):
    uid = message.from_user.id

    if uid not in ADMIN_IDS and get_today_count(uid) >= DAILY_LIMIT:
        bot.send_message(message.chat.id, "🚫 Лимит на сегодня закончился. Загляни завтра 😉")
        return

    user_models.setdefault(uid, "gpt")

    history = get_dialog(uid)
    if not history:
        add_message(uid, "system", system_prompt())

    add_message(uid, "user", message.text)
    inc_today_count(uid)
    history = get_dialog(uid)[-MAX_HISTORY:]

    try:
        answer = providers[user_models[uid]].generate(history)
    except Exception as e:
        answer = f"Хм, что-то пошло не так: {e}"

    add_message(uid, "assistant", answer)
    bot.send_message(message.chat.id, answer)


if __name__ == "__main__":
    Thread(target=daily_reset_loop, daemon=True).start()
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
