import os
import telebot
import re
import sys

# Retrieve token from environment variables safely
BOT_TOKEN = os.getenv8938472941:AAHLT6qkmuFrWEdl8q1YeNUWe6rgyln-VtU")

if not BOT_TOKEN:
    print("❌ ERROR: 'BOT_TOKEN' environment variable is missing!")
    sys.exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# Memory states
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
        f"@NEW_ANIME_HINDI_DUB_OFFICIALL"
    )

    try:
        bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            caption=caption_text,
            parse_mode="Markdown"
        )
        
        if not manual_quality:
            cycle += 1
            if cycle >= 3:
                cycle = 0
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

print("🚀 CAPTION BOT ENGINE RUNNING ONLINE...")
bot.infinity_polling()
