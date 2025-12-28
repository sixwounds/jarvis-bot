import os
from telebot import TeleBot, types
from dotenv import load_dotenv
from nlp_providers import GPTProvider, GeminiProvider, GigaChatProvider
from db import get_dialog, add_message, reset_dialog, get_today_count, inc_today_count, daily_reset_loop
from threading import Thread

load_dotenv()
bot = TeleBot(os.getenv("TELEGRAM_TOKEN"))

ADMIN_IDS = [832410474]
DAILY_LIMIT = 40
MAX_HISTORY = 10

providers = {
    "gpt": GPTProvider(),
    "gemini": GeminiProvider(),
    "gigachat": GigaChatProvider()
}

user_models = {}


def system_prompt():
    return (
        "Тебя зовут Джарвис. Ты харизматичный, живой помощник.\n"
        "Ты никогда не называешь себя нейросетью, ИИ, моделью, GPT, Gemini или GigaChat.\n"
        "Ты говоришь на 'ты', иногда шутишь и поддерживаешь диалог."
    )


@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    user_models[uid] = "gpt"
    reset_dialog(uid)
    add_message(uid, "system", system_prompt())
    bot.send_message(message.chat.id,
        "👋 Привет! Я Джарвис.\n\n"
        "/model — выбор мозга\n"
        "/stats — статистика\n"
        "/reset — очистить память"
    )


@bot.message_handler(commands=["model"])
def choose_model(message):
    kb = types.InlineKeyboardMarkup()
    for m in providers:
        kb.add(types.InlineKeyboardButton(m.upper(), callback_data=m))
    bot.send_message(message.chat.id, "Выбери модель:", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_models[call.from_user.id] = call.data
    bot.answer_callback_query(call.id, f"Теперь активен {call.data.upper()}")


@bot.message_handler(commands=["stats"])
def stats(message):
    used = get_today_count(message.from_user.id)
    bot.send_message(message.chat.id, f"Сегодня использовано {used} из {DAILY_LIMIT}")


@bot.message_handler(commands=["reset"])
def reset(message):
    reset_dialog(message.from_user.id)
    add_message(message.from_user.id, "system", system_prompt())
    bot.send_message(message.chat.id, "Память очищена 🧠")


@bot.message_handler(func=lambda msg: True)
def chat(message):
    uid = message.from_user.id

    if uid not in ADMIN_IDS and get_today_count(uid) >= DAILY_LIMIT:
        bot.send_message(message.chat.id, "Лимит на сегодня исчерпан 😴")
        return

    add_message(uid, "user", message.text)
    inc_today_count(uid)

    history = get_dialog(uid)[-MAX_HISTORY:]
    provider = providers[user_models.get(uid, "gpt")]

    try:
        answer = provider.generate(history)
    except Exception as e:
        answer = f"Ошибка: {e}"

    add_message(uid, "assistant", answer)
    bot.send_message(message.chat.id, answer)


if __name__ == "__main__":
    Thread(target=daily_reset_loop, daemon=True).start()
    bot.infinity_polling()
