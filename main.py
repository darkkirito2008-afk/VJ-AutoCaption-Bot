import telebot
import os
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
# It will now look for "BOT_TOKEN" in Render's Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@NEW_ANIME_HINDI_DUB_OFFICIALL"

if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN variable not found! Please add it in Render Settings.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Global Variables
current_ep = 1
quality_count = 0  

# --- WEB SERVER ---
@app.route('/')
def home(): return "Bot is Running"

def run_web_server():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

# --- BOT COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ **Multi-Quality Batch Bot Active!**\n\n"
                          "Logic: 3 files per episode.\n"
                          "Example: Send 480p, 720p, 1080p for Ep 1, then bot moves to Ep 2.\n\n"
                          "/setep 1 - Start from Episode 1\n"
                          "/skip - Manually move to next episode")

@bot.message_handler(commands=['setep'])
def set_ep(message):
    global current_ep, quality_count
    try:
        num = int(message.text.split()[1])
        current_ep = num
        quality_count = 0
        bot.reply_to(message, f"✅ Restarting from **Episode {current_ep}**")
    except:
        bot.reply_to(message, "Usage: `/setep 1`")

@bot.message_handler(commands=['skip'])
def skip_ep(message):
    global current_ep, quality_count
    current_ep += 1
    quality_count = 0
    bot.reply_to(message, f"⏭ Skipped! Next files will be **Episode {current_ep}**")

# --- MAIN BATCH PROCESSING ---

@bot.message_handler(content_types=['video', 'document'])
def handle_batch(message):
    global current_ep, quality_count
    
    file_info = message.video if message.video else message.document
    file_name = (file_info.file_name or "video").lower()

    # 1. Auto Quality Detection
    quality = "480p [SD]"
    if "1080" in file_name:
        quality = "1080p [FHD]"
    elif "720" in file_name:
        quality = "720p [HD]"
    elif "480" in file_name:
        quality = "480p [SD]"

    # 2. Create Caption
    caption_text = (
        f"Episode :- {current_ep}\n"
        f"🗣 Language :- Hindi Dub\n"
        f"🟡 Quality :- {quality}\n\n"
        f"{CHANNEL_USERNAME}"
    )

    # 3. Send back
    try:
        if message.video:
            bot.send_video(message.chat.id, message.video.file_id, caption=caption_text)
        else:
            bot.send_document(message.chat.id, message.document.file_id, caption=caption_text)
        
        # 4. LOGIC: 3 Qualities per Episode
        quality_count += 1
        if quality_count >= 3:
            current_ep += 1
            quality_count = 0
            
    except Exception as e:
        print(f"Error sending file: {e}")

# --- START ---
if __name__ == "__main__":
    Thread(target=run_web_server).start()
    print("🚀 Bot is starting...")
    bot.infinity_polling()