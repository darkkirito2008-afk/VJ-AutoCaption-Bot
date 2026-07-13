import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Thread
from flask import Flask, request

# --- Flask App ---
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is alive!"

# Bot Token (Best to set as Environment Variable on Render)
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

def progress_bar(current, total):
    percent = (current / total * 100) if total else 0
    bar_length = 15
    filled = int(bar_length * current // total) if total else 0
    bar = '█' * filled + '░' * (bar_length - filled)
    return f"[{bar}] {percent:.1f}%"

@bot.message_handler(commands=['start', 'help'])
def start_help(message):
    text = (
        "👋 **Anime Uploader Bot**\n\n"
        "Commands:\n"
        "/batch - Toggle batch mode\n"
        "/setquality - Choose quality\n"
        "/setepisode - Set episode number\n"
        "/status - Show current status\n"
        "/reset - Reset counters\n\n"
        "Send videos or documents to process."
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
        ep = int(message.text)
        bot.reply_to(message, f"✅ Episode set to **{ep}**", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ Please send a valid number.")

@bot.message_handler(commands=['status'])
def status(message):
    quality = manual_quality or "Auto"
    bot.reply_to(message,
        f"**Current Status**\n"
        f"📌 Episode: {ep}\n"
        f"🎥 Quality: {quality}\n"
        f"📦 Batch Mode: {'ON' if is_batch_mode else 'OFF'}\n"
        f"📊 Processed: {video_counter}",
        parse_mode="Markdown")

@bot.message_handler(commands=['reset'])
def reset(message):
    global video_counter, ep, manual_quality, is_batch_mode
    video_counter = 0
    ep = 1
    manual_quality = None
    is_batch_mode = False
    bot.reply_to(message, "🔄 All settings reset!")

def upload_with_progress(message, quality):
    global video_counter, ep, manual_quality

    msg = bot.reply_to(message, "⬆️ Starting upload... 0%")

    def progress(current, total):
        if total == 0: return
        try:
            bar = progress_bar(current, total)
            bot.edit_message_text(
                f"⬆️ Uploading...\n{bar}\n{current//(1024*1024)}MB / {total//(1024*1024)}MB",
                message.chat.id, msg.message_id
            )
        except:
            pass

    caption = f"Episode :- {ep}\n🗣 Language :- Hindi Dub\n🟡 Quality :- {quality}\n@NEW_ANIME_HINDI_DUB_OFFICIALL"

    try:
        if message.video:
            bot.send_video(
                message.chat.id,
                message.video.file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=get_controls(include_cancel=is_batch_mode),
                progress_hook=progress
            )
        else:
            bot.send_document(
                message.chat.id,
                message.document.file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=get_controls(include_cancel=is_batch_mode),
                progress_hook=progress
            )

        if not manual_quality:
            video_counter += 1
            if video_counter % 3 == 0:
                ep += 1
        else:
            ep += 1

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(content_types=['video', 'document'])
def handle_media(message):
    global manual_quality
    quality = manual_quality or ["480p [SD]", "720p [HD]", "1080p [FHD]"][video_counter % 3]
    Thread(target=upload_with_progress, args=(message, quality), daemon=True).start()

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global manual_quality, video_counter, ep, is_batch_mode

    if call.data.startswith("quality_"):
        manual_quality = call.data.replace("quality_", "")
        bot.answer_callback_query(call.id, f"✅ Quality set: {manual_quality}")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

    elif call.data == "nav_cancel":
        video_counter = 0
        ep = 1
        manual_quality = None
        is_batch_mode = False
        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption="🚫 Batch cancelled and reset.",
            reply_markup=None
        )

    elif call.data == "nav_start":
        bot.answer_callback_query(call.id, f"Ep: {ep} | Quality: {manual_quality or 'Auto'}")

# --- Webhook Route ---
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'ok', 200

if __name__ == "__main__":
    Thread(target=run_web_server, daemon=True).start()
    
    # Remove old webhook and set new one
    bot.remove_webhook()
    webhook_url = os.environ.get("WEBHOOK_URL")
    if webhook_url:
        bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook set: {webhook_url}")
    else:
        print("⚠️ WEBHOOK_URL environment variable not set. Using polling.")
        bot.infinity_polling(skip_pending=True)