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

# --- MEMORY SYSTEM ---
# This saves your progress so Render restarts don't break the count
DATA_FILE = "bot_state.txt"

def save_state(ep, q_idx):
    with open(DATA_FILE, "w") as f:
        f.write(f"{ep},{q_idx}")

def load_state():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = f.read().split(",")
            return int(data[0]), int(data[1])
    return 1, 0  # Default: Episode 1, Quality 480p

# Load state on startup
current_ep, quality_index = load_state()

# --- WEB SERVER ---
@app.route('/')
def home():
    ep, q = load_state()
    return f"Bot Active. Next: Ep {ep}, Quality Index {q} (0=480, 1=720, 2=1080)"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ **Auto-Caption Bot (Fixed Memory Mode)**\n\n"
                          "**Rotation Cycle:**\n"
                          "1. 480p [SD]\n"
                          "2. 720p [HD]\n"
                          "3. 1080p [FHD]\n"
                          "*(Then Episode increases)*\n\n"
                          "Use `/setep 1` to reset everything.")

@bot.message_handler(commands=['setep'])
def set_ep(message):
    global current_ep, quality_index
    try:
        num = int(message.text.split()[1])
        current_ep = num
        quality_index = 0
        save_state(current_ep, quality_index)
        bot.reply_to(message, f"✅ Memory Updated: Starting **Episode {current_ep}** at 480p")
    except:
        bot.reply_to(message, "❌ Error. Use: `/setep 1`")

# --- MEDIA HANDLER ---

@bot.message_handler(content_types=['video', 'document'])
def handle_media(message):
    global current_ep, quality_index
    
    # Reload from file to ensure we are in sync
    current_ep, quality_index = load_state()

    # 1. Determine Quality Tag
    if quality_index == 0:
        quality_tag = "480p [SD]"
    elif quality_index == 1:
        quality_tag = "720p [HD]"
    else:
        quality_tag = "1080p [FHD]"

    # 2. Build the Caption (Matches your screenshot exactly)
    caption = (
        f"Episode :- {current_ep}\n"
        f"🗣 Language :- Hindi Dub\n"
        f"🟡 Quality :- {quality_tag}\n\n"
        f"{CHANNEL_USERNAME}"
    )

    # 3. Send File
    try:
        if message.video:
            bot.send_video(message.chat.id, message.video.file_id, caption=caption)
        else:
            bot.send_document(message.chat.id, message.document.file_id, caption=caption)

        # 4. Increment Quality Index
        quality_index += 1
        
        # 5. Check if Episode is complete (after 3 files)
        if quality_index >= 3:
            current_ep += 1
            quality_index = 0
        
        # 6. Save new state to memory
        save_state(current_ep, quality_index)
            
    except Exception as e:
        print(f"Error: {e}")

# --- STARTUP ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.remove_webhook()
    time.sleep(1)
    print("🚀 Bot Started with Memory Protection")
    bot.infinity_polling()