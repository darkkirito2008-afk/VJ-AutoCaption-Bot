import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import Thread
from flask import Flask

# --- Web Server ---
app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"
def run_web_server(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# Replace 'YOUR_ACTUAL_TOKEN_HERE' with your real token from BotFather
BOT_TOKEN = "8532183235:AAFLyKGjrBdqx4lmaBNe9azT4l_93AJi6R0" 
bot = telebot.TeleBot(BOT_TOKEN)


# State
video_counter = 0
ep = 1
manual_quality = None
is_batch_mode = False

def get_controls(include_cancel=False):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🏠 Menu", callback_data="nav_start"),
        InlineKeyboardButton("⚙️ Quality", callback_data="nav_quality")
    )
    if include_cancel:
        markup.add(InlineKeyboardButton("❌ Cancel Batch", callback_data="nav_cancel"))
    return markup

@bot.message_handler(commands=['batch'])
def toggle_batch(message):
    global is_batch_mode
    is_batch_mode = not is_batch_mode
    status = "ON" if is_batch_mode else "OFF"
    bot.reply_to(message, f"📦 Batch Mode is now **{status}**", parse_mode="Markdown")

@bot.message_handler(content_types=['video', 'document'])
def handle_media(message):
    global video_counter, ep, manual_quality
    media = message.video or message.document
    if not media: return

    quality = manual_quality if manual_quality else ["480p [SD]", "720p [HD]", "1080p [FHD]"][video_counter % 3]
    
    caption = (f"Episode :- {ep}\n🗣 Language :- Hindi Dub\n🟡 Quality :- {quality}\n@NEW_ANIME_HINDI_DUB_OFFICIALL")

    try:
        bot.copy_message(message.chat.id, message.chat.id, message.message_id, 
                         caption=caption, parse_mode="HTML", reply_markup=get_controls(include_cancel=True))
        
        if not manual_quality:
            video_counter += 1
            if video_counter % 3 == 0: ep += 1
        else:
            ep += 1
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("nav_"))
def callback_handler(call):
    global video_counter, ep, manual_quality, is_batch_mode
    
    if call.data == "nav_cancel":
        video_counter, ep, manual_quality, is_batch_mode = 0, 1, None, False
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                                 caption="🚫 Batch cancelled and settings reset.", reply_markup=None)
    
    elif call.data == "nav_start":
        bot.answer_callback_query(call.id, f"Current Ep: {ep} | Quality: {manual_quality or 'Auto'}")
    
    elif call.data == "nav_quality":
        bot.answer_callback_query(call.id, "Use /setquality to change.")

if __name__ == "__main__":
    Thread(target=run_web_server, daemon=True).start()
    bot.infinity_polling(skip_pending=True)
