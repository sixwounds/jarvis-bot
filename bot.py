import os, threading, time
from datetime import datetime
from telebot import TeleBot
from dotenv import load_dotenv
from nlp_providers import GigaChatProvider
from db import get_count, inc_count, reset_day

load_dotenv()

BOT_TOKEN = os.getenv("TG_TOKEN")
ADMIN_ID = 832410474
DAILY_LIMIT = 40

bot = TeleBot(BOT_TOKEN)
ai = GigaChatProvider()


def daily_reset_loop():
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            reset_day()
            time.sleep(65)
        time.sleep(10)


@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(m.chat.id, "Я Джарвис 🤖\nПиши — пообщаемся.")


@bot.message_handler(commands=["stats"])
def stats(m):
    if m.from_user.id != ADMIN_ID:
        return
    bot.send_message(m.chat.id, "Ты администратор. Лимитов нет 👑")


@bot.message_handler(content_types=["text"])
def chat(m):
    uid = m.from_user.id

    if uid != ADMIN_ID:
        if get_count(uid) >= DAILY_LIMIT:
            bot.send_message(m.chat.id, "Ты исчерпал лимит 40 сообщений за сутки 😢")
            return
        inc_count(uid)

    messages = [
        {"role": "system", "content": "Ты дружелюбный ассистент Джарвис."},
        {"role": "user", "content": m.text}
    ]

    try:
        answer = ai.ask(messages)
        bot.send_message(m.chat.id, answer)
    except Exception as e:
        bot.send_message(m.chat.id, f"Ошибка: {e}")


threading.Thread(target=daily_reset_loop, daemon=True).start()
bot.infinity_polling(skip_pending=True)
