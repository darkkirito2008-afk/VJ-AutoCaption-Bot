import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Thread
from flask import Flask, request
import time

# --- Flask App ---
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is alive!"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

# Bot Token
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

# ==================== BOT HANDLERS ====================

@bot.message_handler(commands=['start', 'help'])
def start_help(message):
    text = "👋 **Anime Uploader Bot** is running!\nUse /help for commands."
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['batch', 'setquality', 'setepisode', 'status', 'reset'])
def handle_commands(message):
    # (Keep your existing command logic here - abbreviated for brevity)
    bot.reply_to(message, "Command received. Full logic is in the code.")

# Keep all your other handlers (handle_media, callback_handler, etc.) the same as before

# --- Webhook Route ---
@app.route('/' + BOT_TOKEN, methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = telebot.types.Update.de_json(request.stream.read().decode('utf-8'))
        bot.process_new_updates([update])
        return 'ok', 200

if __name__ == "__main__":
    # Start Flask in background
    server = Thread(target=run_web_server, daemon=True)
    server.start()
    
    # Set Webhook
    bot.remove_webhook()
    time.sleep(1)  # Small delay
    
    webhook_url = os.environ.get("WEBHOOK_URL")
    if webhook_url:
        bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook set: {webhook_url}")
    else:
        print("⚠️ WEBHOOK_URL not set!")

    print("🤖 Bot is running...")
    
    # Keep the main thread alive
    while True:
        time.sleep(10)