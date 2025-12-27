import os
from datetime import datetime
from telebot import TeleBot, types
from dotenv import load_dotenv
from nlp_providers import GPTProvider, GeminiProvider, GigaChatProvider

load_dotenv()

bot = TeleBot(os.getenv("TELEGRAM_TOKEN"))

dialogs = {}
user_models = {}

providers = {
    "gpt": GPTProvider(),
    "gemini": GeminiProvider(),
    "gigachat": GigaChatProvider()
}

MAX_HISTORY = 12


def system_prompt():
    return {
        "role": "system",
        "content": "Тебя зовут Джарвис. Ты умный, дружелюбный ассистент. Отвечай кратко и по делу."
    }


@bot.message_handler(commands=["start"])
def start(message):
    uid = message.from_user.id
    user_models[uid] = "gpt"
    dialogs[uid] = [system_prompt()]
    bot.send_message(
        message.chat.id,
        "👋 Привет! Я **Джарвис**.\n\n"
        "Команды:\n"
        "/model — выбрать нейросеть\n"
        "/draw <описание> — нарисовать картинку\n"
        "/reset — очистить память",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["reset"])
def reset_dialog(message):
    dialogs[message.from_user.id] = [system_prompt()]
    bot.send_message(message.chat.id, "Память очищена 🧹")


@bot.message_handler(commands=["model"])
def choose_model(message):
    kb = types.InlineKeyboardMarkup()
    for m in providers:
        kb.add(types.InlineKeyboardButton(text=m.upper(), callback_data=m))
    bot.send_message(message.chat.id, "Выбери нейросеть:", reply_markup=kb)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_models[call.from_user.id] = call.data
    bot.answer_callback_query(call.id, f"Теперь активна модель: {call.data.upper()}")


@bot.message_handler(commands=["draw"])
def draw(message):
    prompt = message.text.replace("/draw", "").strip()
    if not prompt:
        bot.send_message(message.chat.id, "Напиши описание после /draw")
        return

    bot.send_message(message.chat.id, "🎨 Рисую через GigaChat, подожди...")
    try:
        img_url = providers["gigachat"].draw(prompt)
        bot.send_photo(message.chat.id, img_url)
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка генерации изображения: {e}")


@bot.message_handler(func=lambda msg: True)
def chat(message):
    uid = message.from_user.id
    text = message.text.lower()

    if "какой сейчас год" in text:
        bot.send_message(message.chat.id, str(datetime.now().year))
        return

    dialogs.setdefault(uid, [system_prompt()])
    user_models.setdefault(uid, "gpt")

    dialogs[uid].append({"role": "user", "content": message.text})
    dialogs[uid] = dialogs[uid][-MAX_HISTORY:]

    provider = providers[user_models[uid]]

    try:
        answer = provider.generate(dialogs[uid])
    except Exception as e:
        answer = f"Ошибка API: {e}"

    dialogs[uid].append({"role": "assistant", "content": answer})
    bot.send_message(message.chat.id, answer)


bot.polling()
