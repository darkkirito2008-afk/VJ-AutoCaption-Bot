import telebot
import os
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
# IMPORTANT: Ensure 'BOT_TOKEN' is added in Render -> Settings -> Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@NEW_ANIME_HINDI_DUB_OFFICIALL"

# Simple check to stop if token is missing
if not BOT_TOKEN:
    print("❌ BOT_TOKEN is missing in Environment Variables!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Global Variables
current_ep = 1
quality_count = 0  

# --- WEB SERVER (To keep Render happy) ---
@app.route('/')
def home():
    return "Bot is alive and running!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ **Bot is Active!**\n\nI will count 3 qualities per episode.\nUse `/setep 1` to start.")

@bot.message_handler(commands=['setep'])
def set_ep(message):
    global current_ep, quality_count
    try:
        num = int(message.text.split()[1])
        current_ep = num
        quality_count = 0
        bot.reply_to(message, f"✅ Starting from **Episode {current_ep}**")
    except:
        bot.reply_to(message, "Usage: `/setep 1`")

@bot.message_handler(content_types=['video', 'document'])
def handle_media(message):
    global current_ep, quality_count
    
    try:
        file_info = message.video if message.video else message.document
        file_name = (file_info.file_name or "video").lower()

        # 1. Detect Quality
        quality = "480p [SD]"
        if "1080" in file_name: quality = "1080p [FHD]"
        elif "720" in file_name: quality = "720p [HD]"

        # 2. Caption
        caption = (
            f"Episode :- {current_ep}\n"
            f"🗣 Language :- Hindi Dub\n"
            f"🟡 Quality :- {quality}\n\n"
            f"{CHANNEL_USERNAME}"
        )

        # 3. Send
        if message.video:
            bot.send_video(message.chat.id, message.video.file_id, caption=caption)
        else:
            bot.send_document(message.chat.id, message.document.file_id, caption=caption)

        # 4. Count logic (3 files per episode)
        quality_count += 1
        if quality_count >= 3:
            current_ep += 1
            quality_count = 0

    except Exception as e:
        print(f"Error: {e}")

# --- EXECUTION ---
if __name__ == "__main__":
    # Start the web server in a thread
    server_thread = Thread(target=run_web)
    server_thread.start()
    
    print("🚀 Bot is starting polling...")
    # This keeps the bot listening to Telegram
    bot.infinity_polling(timeout=10, long_polling_timeout=5)