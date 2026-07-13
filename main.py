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

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8532183235:AAFLyKGjrBdqx4lmaBNe9azT4l_93AJi6R0")
bot = telebot.TeleBot(BOT_TOKEN)

# Global State
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

@bot.message_handler(commands=['start', 'help'])
def start_help(message):
    text = (
        "👋 **Anime Uploader Bot**\n\n"
        "Commands:\n"
        "/batch - Toggle batch mode\n"
        "/setquality - Choose quality\n"
        "/setepisode - Set episode number\n"
        "/status - Show status\n"
        "/reset or /restart - Reset everything"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['batch'])
def toggle_batch(message):
    global is_batch_mode
    is_batch_mode = not is_batch_mode
    bot.reply_to(message, f"📦 Batch Mode: **{'ON' if is_batch_mode else 'OFF'}**", parse_mode="Markdown")

@bot.message_handler(commands=['setquality'])
def set_quality(message):
    markup = InlineKeyboardMarkup(row_width=2)
    qualities = ["480p [SD]", "720p [HD]", "1080p [FHD]", "1440p [QHD]", "2160p [4K]"]
    for q in qualities:
        markup.add(InlineKeyboardButton(q, callback_data=f"quality_{q}"))
    bot.reply_to(message, "🎥 Select Quality:", reply_markup=markup)

@bot.message_handler(commands=['setepisode'])
def set_episode(message):
    msg = bot.reply_to(message, "📝 Send new episode number:")
    bot.register_next_step_handler(msg, process_episode)

def process_episode(message):
    global ep
    try:
        ep = int(message.text.strip())
        bot.reply_to(message, f"✅ Episode number saved as **{ep}**", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Please send a valid number.")

@bot.message_handler(commands=['status'])
def status(message):
    quality = manual_quality or "Auto"
    bot.reply_to(message, f"**Status**\n📌 Episode: {ep}\n🎥 Quality: {quality}\n📦 Batch: {'ON' if is_batch_mode else 'OFF'}", parse_mode="Markdown")

@bot.message_handler(commands=['reset', 'restart'])
def reset(message):
    global video_counter, ep, manual_quality, is_batch_mode
    video_counter = 0
    ep = 1
    manual_quality = None
    is_batch_mode = False
    bot.reply_to(message, "🔄 Everything has been reset! Episode is now 1.")

def upload_media(message, quality):
    global video_counter, ep, manual_quality
    status_msg = bot.reply_to(message, "⬆️ Uploading... Please wait.")

    caption = f"Episode :- {ep}\n🗣 Language :- Hindi Dub\n🟡 Quality :- {quality}\n@NEW_ANIME_HINDI_DUB_OFFICIALL"

    try:
        if message.video:
            bot.send_video(message.chat.id, message.video.file_id, caption=caption, parse_mode="HTML",
                           reply_markup=get_controls(include_cancel=is_batch_mode))
        else:
            bot.send_document(message.chat.id, message.document.file_id, caption=caption, parse_mode="HTML",
                              reply_markup=get_controls(include_cancel=is_batch_mode))

        if not manual_quality:
            video_counter += 1
            if video_counter % 3 == 0:
                ep += 1
        else:
            ep += 1

        bot.edit_message_text("✅ Upload Complete!", message.chat.id, status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, status_msg.message_id)

@bot.message_handler(content_types=['video', 'document'])
def handle_media(message):
    global manual_quality
    quality = manual_quality or ["480p [SD]", "720p [HD]", "1080p [FHD]"][video_counter % 3]
    Thread(target=upload_media, args=(message, quality), daemon=True).start()

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global manual_quality, video_counter, ep, is_batch_mode

    if call.data.startswith("quality_"):
        manual_quality = call.data.replace("quality_", "")
        bot.answer_callback_query(call.id, f"✅ Quality: {manual_quality}")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    elif call.data == "nav_cancel":
        video_counter = 0
        ep = 1
        manual_quality = None
        is_batch_mode = False
        bot.edit_message_caption(call.message.chat.id, call.message.message_id, 
                                 caption="🚫 Batch cancelled and reset.", reply_markup=None)

if __name__ == "__main__":
    Thread(target=run_web_server, daemon=True).start()
    
    bot.remove_webhook()
    time.sleep(1)
    
    webhook_url = os.environ.get("WEBHOOK_URL")
    if webhook_url:
        bot.set_webhook(url=webhook_url)
        print("✅ Webhook set")
    
    print("🤖 Bot running...")
    while True:
        time.sleep(10)