cat << 'EOF' > bot.py
import telebot
import re

# Initialize the Python Bot engine with your token
BOT_TOKEN = "8642173946:AAECP4OSifEKjCbuhK_VkfCQf8jcrMowK44"
bot = telebot.TeleBot(BOT_TOKEN)

# Memory states
ep = 1
cycle = 0
last_processed_file_id = ""
manual_quality = None

@bot.message_handler(content_types=['video', 'document', 'text'], func=lambda message: True)
def handle_all_media(message):
    global ep, cycle, last_processed_file_id, manual_quality
    
    if message.text and message.text.startswith('/'):
        return

    media = None
    if message.video:
        media = message.video
    elif message.document:
        media = message.document
    
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

    status_msg = bot.reply_to(message, "Processing and adding caption... ⏳")

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
        print(f"Error: {e}")
        bot.send_message(message.chat.id, "❌ Failed to add caption to this file.")

    try:
        bot.delete_message(message.chat.id, status_msg.message_id)
    except:
        pass

@bot.message_handler(commands=['start'])
def command_start(message):
    if manual_quality:
        q = f"{manual_quality} (MANUAL LOCK)"
    else:
        q = "480p SD" if cycle == 0 else "720p HD" if cycle == 1 else "1080p FHD"
    bot.reply_to(message, f"👋 **Bot Status:**\n\n🔢 Next Episode: `Episode {ep}`\n🟡 Next Quality: `{q}`", parse_mode="Markdown")

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
        bot.reply_to(message, "✅ Quality locked to: **480p SD**\n(Auto-rotation disabled)", parse_mode="Markdown")
    elif "720" in text:
        manual_quality = "720p HD"
        bot.reply_to(message, "✅ Quality locked to: **720p HD**\n(Auto-rotation disabled)", parse_mode="Markdown")
    elif "1080" in text:
        manual_quality = "1080p FHD"
        bot.reply_to(message, "✅ Quality locked to: **1080p FHD**\n(Auto-rotation disabled)", parse_mode="Markdown")
    elif "auto" in text or "reset" in text:
        manual_quality = None
        cycle = 0
        bot.reply_to(message, "🔄 Back to standard **Auto-Rotation Mode**.")
    else:
        bot.reply_to(message, "❌ Provide a specific quality setup!\nExamples: `/setquality 720` or `/setquality auto`")

@bot.message_handler(commands=['restart'])
def command_restart(message):
    global ep, cycle, last_processed_file_id, manual_quality
    ep = 1
    cycle = 0
    manual_quality = None
    last_processed_file_id = ""
    bot.reply_to(message, "🔄 Bot memory reset completely!")

print("🚀 PRODUCTION AUTO-CAPTION ENGINE ACTIVE...")
bot.infinity_polling()
EOF
