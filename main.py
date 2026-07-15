import telebot
import os
from flask import Flask
from threading import Thread

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@NEW_ANIME_HINDI_DUB_OFFICIALL"

if not BOT_TOKEN:
    print("❌ BOT_TOKEN is missing!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Global Variables
current_ep = 1
quality_count = 0  # 0 = 480p, 1 = 720p, 2 = 1080p

# --- WEB SERVER ---
@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ **Batch Rotation Bot Active!**\n\n"
                          "**Current Logic:**\n"
                          "1st file sent = 480p [SD]\n"
                          "2nd file sent = 720p [HD]\n"
                          "3rd file sent = 1080p [FHD]\n"
                          "Then it moves to the next episode automatically.\n\n"
                          "Use `/setep 1` to reset.")

@bot.message_handler(commands=['setep'])
def set_ep(message):
    global current_ep, quality_count
    try:
        num = int(message.text.split()[1])
        current_ep = num
        quality_count = 0  # Reset quality to 480p
        bot.reply_to(message, f"✅ Restarting from **Episode {current_ep} (480p)**")
    except:
        bot.reply_to(message, "Usage: `/setep 1`")

@bot.message_handler(content_types=['video', 'document'])
def handle_media(message):
    global current_ep, quality_count
    
    try:
        # --- QUALITY ROTATION LOGIC ---
        if quality_count == 0:
            quality = "480p [SD]"
        elif quality_count == 1:
            quality = "720p [HD]"
        else:
            quality = "1080p [FHD]"

        # Create Caption
        caption = (
            f"Episode :- {current_ep}\n"
            f"🗣 Language :- Hindi Dub\n"
            f"🟡 Quality :- {quality}\n\n"
            f"{CHANNEL_USERNAME}"
        )

        # Send File
        if message.video:
            bot.send_video(message.chat.id, message.video.file_id, caption=caption)
        else:
            bot.send_document(message.chat.id, message.document.file_id, caption=caption)

        # Update Counters
        quality_count += 1
        
        # If we reached 3 files, move to next episode and reset quality to 480p
        if quality_count >= 3:
            current_ep += 1
            quality_count = 0

    except Exception as e:
        print(f"Error: {e}")

# --- EXECUTION ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    
    print("🚀 Removing old webhooks...")
    bot.remove_webhook() 
    
    print("🚀 Bot is starting polling...")
    bot.infinity_polling()