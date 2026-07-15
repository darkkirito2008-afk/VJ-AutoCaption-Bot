import telebot
import os
from flask import Flask
from threading import Thread
import time

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@NEW_ANIME_HINDI_DUB_OFFICIALL"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# --- GLOBAL COUNTERS ---
# These will reset to 1 and 0 if the bot restarts on Render
current_ep = 1
quality_index = 0  # 0=480p, 1=720p, 2=1080p

# --- WEB SERVER ---
@app.route('/')
def home():
    return f"Bot is Active. Current Ep: {current_ep}, Next Quality Index: {quality_index}"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🔥 **Auto Caption Bot with 3-Quality Rotation**\n\n"
                          "**How it works:**\n"
                          "1. Send 480p file -> Gets 480p caption\n"
                          "2. Send 720p file -> Gets 720p caption\n"
                          "3. Send 1080p file -> Gets 1080p caption\n"
                          "4. Next file -> Becomes next Episode (480p)\n\n"
                          "Use `/setep 1` to reset anytime.")

@bot.message_handler(commands=['setep'])
def set_ep(message):
    global current_ep, quality_index
    try:
        num = int(message.text.split()[1])
        current_ep = num
        quality_index = 0
        bot.reply_to(message, f"✅ Restarting from **Episode {current_ep}** (Quality: 480p)")
    except:
        bot.reply_to(message, "❌ Use: `/setep 1`")

# --- MEDIA HANDLER ---

@bot.message_handler(content_types=['video', 'document'])
def handle_media(message):
    global current_ep, quality_index
    
    # 1. Determine Quality Tag based on Rotation
    if quality_index == 0:
        quality_tag = "480p [SD]"
    elif quality_index == 1:
        quality_tag = "720p [HD]"
    else:
        quality_tag = "1080p [FHD]"

    # 2. Build the Caption
    caption = (
        f"Episode :- {current_ep}\n"
        f"🗣 Language :- Hindi Dub\n"
        f"🟡 Quality :- {quality_tag}\n\n"
        f"{CHANNEL_USERNAME}"
    )

    # 3. Send the File
    try:
        if message.video:
            bot.send_video(message.chat.id, message.video.file_id, caption=caption)
        else:
            bot.send_document(message.chat.id, message.document.file_id, caption=caption)

        # 4. Update the Counters
        quality_index += 1
        
        # After 3 qualities, move to next Episode and back to 480p
        if quality_index >= 3:
            current_ep += 1
            quality_index = 0
            
    except Exception as e:
        print(f"Error: {e}")

# --- STARTUP ---
if __name__ == "__main__":
    # Start Web Server
    Thread(target=run_web).start()
    
    # Fix Conflict Error
    print("🚀 Clearing old webhooks...")
    bot.remove_webhook()
    time.sleep(1)
    
    print(f"🚀 Bot started! Current Episode: {current_ep}")
    bot.infinity_polling()