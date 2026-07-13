import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Thread
from flask import Flask, request
import time

app = Flask(__name__)

# ====================== WEBHOOK ROUTE ======================
@app.route('/')
def home():
    return "✅ Bot is alive!"

@app.route('/' + os.environ.get("BOT_TOKEN", "8532183235:AAFLyKGjrBdqx4lmaBNe9azT4l_93AJi6R0"), methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'ok', 200

# ====================== BOT SETUP ======================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8532183235:AAFLyKGjrBdqx4lmaBNe9azT4l_93AJi6R0")
bot = telebot.TeleBot(BOT_TOKEN)

video_counter = 0
ep = 1
manual_quality = None
is_batch_mode = False

def get_controls(include_cancel=False):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🏠 Menu", callback_data="nav_start"),
        InlineKeyboardButton("⚙️ Quality", callback_data="nav_quality")
    )
    if include_cancel:
        markup.add(InlineKeyboardButton("❌ Cancel Batch", callback_data="nav_cancel"))
    return markup

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

# ====================== COMMANDS ======================
@bot.message_handler(commands=['start', 'help'])
def start_help(message):
    bot.reply_to(message, "👋 Bot Ready!\nUse /setepisode, /status, /reset etc.")

@bot.message_handler(commands=['setepisode'])
def set_episode(message):
    msg = bot.reply_to(message, "📝 Send new episode number:")
    bot.register_next_step_handler(msg, process_episode)

def process_episode(message):
    global ep
    try:
        ep = int(message.text.strip())
        bot.reply_to(message, f"✅ Episode set to **{ep}**", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Invalid number!")

@bot.message_handler(commands=['status'])
def status(message):
    bot.reply_to(message, f"Current Episode: **{ep}**", parse_mode="Markdown")

@bot.message_handler(commands=['reset', 'restart'])
def reset_bot(message):
    global video_counter, ep, manual_quality, is_batch_mode
    video_counter = 0
    ep = 1
    manual_quality = None
    is_batch_mode = False
    bot.reply_to(message, "🔄 Reset done! Episode = 1")

def upload_media(message, quality):
    global ep
    status_msg = bot.reply_to(message, "⬆️ Uploading...")

    caption = f"Episode :- {ep}\n🗣 Language :- Hindi Dub\n🟡 Quality :- {quality}\n@NEW_ANIME_HINDI_DUB_OFFICIALL"

    try:
        if message.video:
            bot.send_video(message.chat.id, message.video.file_id, caption=caption, parse_mode="HTML")
        else:
            bot.send_document(message.chat.id, message.document.file_id, caption=caption, parse_mode="HTML")
        bot.edit_message_text("✅ Done!", message.chat.id, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ {str(e)}", message.chat.id, status_msg.message_id)

@bot.message_handler(content_types=['video', 'document'])
def handle_media(message):
    quality = manual_quality or "480p [SD]"
    Thread(target=upload_media, args=(message, quality), daemon=True).start()

if __name__ == "__main__":
    Thread(target=run_web_server, daemon=True).start()
    
    bot.remove_webhook()
    time.sleep(2)
    
    webhook_url = os.environ.get("WEBHOOK_URL")
    if webhook_url:
        bot.set_webhook(url=webhook_url)
        print("Webhook set successfully")
    else:
        print("No WEBHOOK_URL set")

    print("Bot is running...")
    while True:
        time.sleep(10)