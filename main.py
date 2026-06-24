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
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 2. Main Telegram Bot Logic
BOT_TOKEN = "8938472941:AAEIgq4jLypp2HXj_tzYGl_8hTlNwQbMm3Q"
bot = telebot.TeleBot(BOT_TOKEN)

ep = 1
cycle = 0
last_processed_file_id = ""
manual_quality = None

@bot.message_handler(content_types=['video', 'document'], func=lambda message: True)
def handle_incoming_media(message):
    global ep, cycle, last_processed_file_id, manual_quality
    
    media = message.video or message.document
    if not media:
        return
        
    file_id = media.file_id
    if file_id == last_processed_file_id:
        return
    last_processed_file_id = file_id

    # Determine current quality block instantly
    if manual_quality:
        quality = manual_quality
    else:
        if cycle == 0:
            quality = "480p SD"
        elif cycle == 1:
            quality = "720p HD"
        else:
            quality = "1080p FHD"

    caption_text = (
        f"Episode :- {ep}\n"
        f"🗣 Language :- Hindi Dub\n"
        f"🟡 Quality :- {quality}\n"
        f"@NEW\_ANIME\_HINDI\_DUB\_OFFICIALL"
    )

    # CRITICAL FIX: Advance counter tracking variables immediately BEFORE sending the message payload
    if not manual_quality:
        cycle += 1
        if cycle >= 3:
            cycle = 0
            ep += 1
    else:
        ep += 1

    try:
        bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            caption=caption_text,
            parse_mode="Markdown"
        )
            
    except Exception as e:
        print(f"Error handling media: {e}")

@bot.message_handler(commands=['start'])
def command_start(message):
    if manual_quality:
        q = f"{manual_quality} (MANUAL LOCK)"
    else:
        q = "480p SD" if cycle == 0 else "720p HD" if cycle == 1 else "1080p FHD"
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
    global manual_quality, cycle
    text = message.text.lower()
    
    if "480" in text:
        manual_quality = "480p SD"
        bot.reply_to(message, "✅ Quality locked to: **480p SD**")
    elif "720" in text:
        manual_quality = "720p HD"
        bot.reply_to(message, "✅ Quality locked to: **720p HD**")
    elif "1080" in text:
        manual_quality = "1080p FHD"
        bot.reply_to(message, "✅ Quality locked to: **1080p FHD**")
    elif "auto" in text or "reset" in text:
        manual_quality = None
        cycle = 0
        bot.reply_to(message, "🔄 Restored to automatic **Auto-Rotation Mode**.")
    else:
        bot.reply_to(message, "❌ Provide a quality level!\nExamples: `/setquality 720` or `/setquality auto`")

@bot.message_handler(commands=['restart'])
def command_restart(message):
    global ep, cycle, last_processed_file_id, manual_quality
    ep = 1
    cycle = 0
    manual_quality = None
    last_processed_file_id = ""
    bot.reply_to(message, "🔄 Bot system memory fully reset to Episode 1!")

if __name__ == "__main__":
    server_thread = Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("🚀 CAPTION BOT ENGINE ACTIVE & WEB PORT OPEN...")
    bot.infinity_polling()
