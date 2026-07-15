import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Thread
from flask import Flask, request
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is alive!"

@app.route('/' + os.environ.get("BOT_TOKEN", ""), methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
    bot.process_new_updates([update])
    return 'ok', 200

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8553087059:AAGesMcoHFcjf0-o5o9VGH213gP_Y3rfkVU")
bot = telebot.TeleBot(BOT_TOKEN)

# State
ep = 1
manual_quality = None
video_counter = 0

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot Ready!\n/setepisode - Set episode\n/setquality - Set quality\n/status - Check")

@bot.message_handler(commands=['setepisode'])
def set_episode(message):
    msg = bot.reply_to(message, "Send new episode number:")
    bot.register_next_step_handler(msg, save_ep)

def save_ep(message):
    global ep
    try:
        ep = int(message.text)
        bot.reply_to(message, f"✅ Episode set to {ep}")
    except:
        bot.reply_to(message, "Invalid!")

@bot.message_handler(commands=['setquality'])
def set_quality(message):
    markup = InlineKeyboardMarkup(row_width=1)
    for q in ["480p [SD]", "720p [HD]", "1080p [FHD]"]:
        markup.add(InlineKeyboardButton(q, callback_data="q_" + q))
    bot.reply_to(message, "Choose Quality:", reply_markup=markup)

@bot.message_handler(commands=['status'])
def status(message):
    q = manual_quality or "Auto Rotate"
    bot.reply_to(message, f"Episode: {ep}\nQuality: {q}")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    global manual_quality
    if call.data.startswith("q_"):
        manual_quality = call.data[2:]
        bot.answer_callback_query(call.id, f"Quality locked to {manual_quality}")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

def upload(message):
    global ep, video_counter

    qualities = [
        "480p [SD]",
        "720p [HD]",
        "1080p [FHD]"
    ]

    quality = qualities[video_counter]

    caption = f"""Episode :- {ep}
🗣 Language :- Hindi Dub
🟡 Quality :- {quality}

@NEW_ANIME_HINDI_DUB_OFFICIALL"""

    try:
        if message.video:
            bot.send_video(message.chat.id, message.video.file_id, caption=caption)
        else:
            bot.send_document(message.chat.id, message.document.file_id, caption=caption)

        video_counter += 1

        if video_counter >= 3:
            video_counter = 0
            ep += 1

    except Exception as e:
        bot.reply_to(message, f"Error: {e}")