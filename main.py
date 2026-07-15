import telebot
import os
from flask import Flask
from threading import Thread
import time

# --- CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_USERNAME = "@NEW_ANIME_HINDI_DUB_OFFICIALL"

# Set threaded=True to handle multiple videos at once
bot = telebot.TeleBot(BOT_TOKEN, threaded=True, num_threads=5)
app = Flask(__name__)

# --- PERMANENT MEMORY ---
DATA_FILE = "bot_state.txt"

def save_state(ep, q_idx):
    try:
        with open(DATA_FILE, "w") as f:
            f.write(f"{ep},{q_idx}")
    except Exception as e:
        print(f"Save error: {e}")

def load_state():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = f.read().split(",")
                return int(data[0]), int(data[1])
        except:
            pass
    return 1, 0

# --- WEB SERVER ---
@app.route('/')
def home():
    ep, q = load_state()
    return f"Bot Running. Next: Ep {ep}, Qual Index {q}"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "ʜᴇʟʟᴏ sᴇɴᴘᴀɪ, ʜᴏᴡ ᴍᴜᴄʜ ᴡɪʟʟ ᴜ ᴇᴅɪᴛ ᴄᴀᴘᴛɪᴏɴ\n\n"
                          "1. 480p [SD]\n"
                          "2. 720p [HD]\n"
                          "3. 1080p [FHD]\n"
                          "*(Automatic Rotation)*\n\n"
                          "Commands:\n"
                          "/setep 10 - Start from Ep 10\n"
                          "/restart - Reset all to Ep 1 & 480p")

@bot.message_handler(commands=['restart'])
def restart_bot(message):
    save_state(1, 0)
    bot.reply_to(message, "🔄 **Bot Reset!** Starting from Episode 1 (480p) again.")

@bot.message_handler(commands=['setep'])
def set_ep(message):
    try:
        num = int(message.text.split()[1])
        save_state(num, 0)
        bot.reply_to(message, f"✅ Episode set to **{num}** (Starting at 480p)")
    except:
        bot.reply_to(message, "❌ Use: `/setep 10`")

# --- MEDIA HANDLER (Optimized for Batch) ---

@bot.message_handler(content_types=['video', 'document'])
def handle_media(message):
    # Load state at the start of every message processing
    ep, q_idx = load_state()
    
    # 1. Select Quality
    tags = ["480p [SD]", "720p [HD]", "1080p [FHD]"]
    current_tag = tags[q_idx]

    # 2. Build Caption
    caption = (
        f"Episode :- {ep}\n"
        f"🗣 Language :- Hindi Dub\n"
        f"🟡 Quality :- {current_tag}\n\n"
        f"{CHANNEL_USERNAME}"
    )

    try:
        # 3. Send Media
        if message.video:
            bot.send_video(message.chat.id, message.video.file_id, caption=caption)
        else:
            bot.send_document(message.chat.id, message.document.file_id, caption=caption)

        # 4. Update index and save IMMEDIATELY
        q_idx += 1
        if q_idx >= 3:
            ep += 1
            q_idx = 0
        
        save_state(ep, q_idx)
        
        # Small delay to prevent Render from getting overwhelmed during batches
        time.sleep(1)
            
    except Exception as e:
        print(f"Batch Error: {e}")

# --- STARTUP ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.remove_webhook()
    time.sleep(1)
    print("🚀 Bot Started Successfully")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)