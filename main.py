import os
import telebot
import re
import sys
from threading import Thread
from flask import Flask

# 1. Dummy web server for Render's port scanner
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_web_server():
    # Force dynamic port binding for Render's requirements
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. Main Telegram Bot Logic
BOT_TOKEN = "8553087059:AAH88LMKUIv4UuDduE1dv_BCFHb2C-Gtwug"
bot = telebot.TeleBot(BOT_TOKEN)

# Global trackers
video_counter = 0  # Total videos processed overall
ep = 1             # Episode tracker
manual_quality = None

@bot.message_handler(content_types=['video', 'document'], func=lambda message: True)
def handle_incoming_media(message):
    global video_counter, ep, manual_quality
    
    media = message.video or message.document
    if not media:
        return

    # Calculate exact quality loop stage with escaped markdown brackets
    if manual_quality:
        quality = manual_quality
    else:
        remainder = video_counter % 3
        if remainder == 0:
            quality = "480p \[SD\]"
        elif remainder == 1:
            quality = "720p \[HD\]"
        else:
            quality = "1080p \[FHD\]"

    caption_text = (
        f"Episode :- {ep}\n"
        f"🗣 Language :- Hindi Dub\n"
        f"🟡 Quality :- {quality}\n"
        f"@NEW\_ANIME\_HINDI\_DUB\_OFFICIALL"
    )

    try:
        # Deliver the copied file with formatting intact
        bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            caption=caption_text,
            parse_mode="Markdown"
        )
        
        # Safe structural state updates
        if not manual_quality:
            video_counter += 1
            # Every 3 videos completed means one full episode set is done
            if video_counter % 3 == 0:
                ep += 1
        else:
            ep += 1
            
    except Exception as e:
        print(f"Error handling media: {e}")

@bot.message_handler(commands=['start'])
def command_start(message):
    if manual_quality:
        q = f"{manual_quality} (MANUAL LOCK)"
    else:
        remainder = video_counter % 3
        q = "480p \[SD\]" if remainder == 0 else "720p \[HD\]" if remainder == 1 else "1080p \[FHD\]"
    status = f"👋 **Bot Status:**\n\n🔢 Next Episode: `Episode {ep}`\n🟡 Next Quality: `{q}`"
    bot.reply_to(message, status, parse_mode="Markdown")

@bot.message_handler(commands=['setep'])
def command_setep(message):
    global ep
    match = re.search(r'\d+', message.text)
    if match:
        ep = int(match.group())
        bot.reply_to(message, f"✅ Next episode target set manually to: Episode {ep}")
    else:
        bot.reply_to(message, "❌ Use format: /setep 15")

@bot.message_handler(commands=['setquality'])
def command_setquality(message):
    global manual_quality, video_counter
    text = message.text.lower()
    
    if "480" in text:
        manual_quality = "480p \[SD\]"
        bot.reply_to(message, "✅ Quality locked to: **480p [SD]**")
    elif "720" in text:
        manual_quality = "720p \[HD\]"
        bot.reply_to(message, "✅ Quality locked to: **720p [HD]**")
    elif "1080" in text:
        manual_quality = "1080p \[FHD\]"
        bot.reply_to(message, "✅ Quality locked to: **1080p [FHD]**")
    elif "auto" in text or "reset" in text:
        manual_quality = None
        video_counter = 0
        bot.reply_to(message, "🔄 Restored to automatic **Auto-Rotation Mode** starting at 480p.")
    else:
        bot.reply_to(message, "❌ Provide a quality level!\nExamples: `/setquality 720` or `/setquality auto`")

@bot.message_handler(commands=['restart'])
def command_restart(message):
    global ep, video_counter, manual_quality
    ep = 1
    video_counter = 0
    manual_quality = None
    bot.reply_to(message, "🔄 Bot system memory fully reset to Episode 1 & 480p [SD]!")

if __name__ == "__main__":
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("🚀 CAPTION BOT ENGINE ACTIVE & WEB PORT OPEN...")
    bot.infinity_polling()
