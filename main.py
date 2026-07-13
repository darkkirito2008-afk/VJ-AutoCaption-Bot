import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Thread
from flask import Flask, request
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot Alive"

@app.route('/' + os.environ.get("BOT_TOKEN", "8532183235:AAFLyKGjrBdqx4lmaBNe9azT4l_93AJi6R0"), methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok', 200

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8532183235:AAFLyKGjrBdqx4lmaBNe9azT4l_93AJi6R0")
bot = telebot.TeleBot(BOT_TOKEN)

# State
ep = 1
manual_quality = None

def get_controls():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🏠 Menu", callback_data="menu"))
    return markup

@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot.reply_to(message, "Bot Ready!\n/setepisode - change episode\n/setquality - change quality\n/status - check")

@bot.message_handler(commands=['setepisode'])
def set_episode(message):
    msg = bot.reply_to(message, "Send new episode number:")
    bot.register_next_step_handler(msg, save_episode)

def save_episode(message):
    global ep
    try:
        ep = int(message.text)
        bot.reply_to(message, f"✅ Episode set to {ep}")
    except:
        bot.reply_to(message, "Invalid number")

@bot.message_handler(commands=['setquality'])
def set_quality(message):
    markup = InlineKeyboardMarkup()
    for q in ["480p [SD]", "720p [HD]", "1080p [FHD]"]:
        markup.add(InlineKeyboardButton(q, callback_data="q_" + q))
    bot.reply_to(message, "Choose Quality:", reply_markup=markup)

@bot.message_handler(commands=['status'])
def status(message):
    bot.reply_to(message, f"Current Episode: {ep}\nQuality: {manual_quality or 'Auto'}")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    global manual_quality
    if call.data.startswith("q_"):
        manual_quality = call.data[2:]
        bot.answer_callback_query(call.id, f"Quality set to {manual_quality}")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

def upload(message):
    global ep
    quality = manual_quality or "480p [SD]"
    caption = f"Episode :- {ep}\nLanguage :- Hindi Dub\nQuality :- {quality}\n@NEW_ANIME_HINDI_DUB_OFFICIALL"

    try:
        if message.video:
            bot.send_video(message.chat.id, message.video.file_id, caption=caption, parse_mode="HTML")
        else:
            bot.send_document(message.chat.id, message.document.file_id, caption=caption, parse_mode="HTML")
        bot.reply_to(message, "✅ Uploaded with current settings.")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@bot.message_handler(content_types=['video', 'document'])
def handle(message):
    Thread(target=upload, args=(message,), daemon=True).start()

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000))), daemon=True).start()
    bot.remove_webhook()
    time.sleep(1)
    if os.environ.get("WEBHOOK_URL"):
        bot.set_webhook(os.environ.get("WEBHOOK_URL"))
    print("Bot Started")
    while True:
        time.sleep(10)