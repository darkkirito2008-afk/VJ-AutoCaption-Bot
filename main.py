import os
import json
import time
import logging
import threading
from flask import Flask, request

import telebot
from telebot import types


# =========================
# LOGGING
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# =========================
# CONFIG
# =========================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing in Render Environment")


bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


PORT = int(os.environ.get("PORT", 10000))

WEBHOOK_URL = os.environ.get(
    "WEBHOOK_URL",
    "https://vj-autocaption-bot-u1il.onrender.com"
)


# =========================
# FLASK SERVER
# =========================

app = Flask(__name__)


@app.route("/")
def home():
    return "Auto Caption Bot Running ✅"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():

    try:
        json_data = request.get_json()

        update = types.Update.de_json(json_data)

        bot.process_new_updates([update])

        return "OK", 200

    except Exception as e:
        logger.error(
            f"Webhook error: {e}"
        )

        return "ERROR", 500



# =========================
# DATA STORAGE
# =========================

DATA_FILE = "data.json"


def load_data():

    if not os.path.exists(DATA_FILE):

        return {
            "episode": 1,
            "qualities": {}
        }

    with open(DATA_FILE, "r") as f:
        return json.load(f)



def save_data(data):

    with open(DATA_FILE, "w") as f:
        json.dump(
            data,
            f,
            indent=4
        )


data = load_data()



# =========================
# START COMMAND
# =========================


@bot.message_handler(commands=["start"])
def start(message):

    bot.reply_to(
        message,
        """
<b>🎬 Auto Caption Bot</b>

Bot is online ✅

Commands:

/caption - Set caption
/status - Check episode
/restart - Restart counter
"""
    )


# END PART 1
# =========================
# QUALITY SYSTEM
# =========================

QUALITY_LIST = {
    "480p": "480p [SD]",
    "720p": "720p [HD]",
    "1080p": "1080p [FHD]"
}


def get_quality_buttons():

    markup = types.InlineKeyboardMarkup()

    markup.row(
        types.InlineKeyboardButton(
            "480p [SD]",
            callback_data="quality_480p"
        ),
        types.InlineKeyboardButton(
            "720p [HD]",
            callback_data="quality_720p"
        )
    )

    markup.row(
        types.InlineKeyboardButton(
            "1080p [FHD]",
            callback_data="quality_1080p"
        )
    )

    return markup



# =========================
# CAPTION GENERATOR
# =========================

def create_caption(
    episode,
    quality
):

    caption = f"""
<b>[@Anicore_Animes] MHA : Vigilantes S02 E{episode:02d}</b>


Episode :- {episode}

🗣 Language :- Hindi Dub
🟡 Quality :- {quality}


@NEW_ANIME_HINDI_DUB_OFFICIALL
"""

    return caption



# =========================
# STATUS COMMAND
# =========================

@bot.message_handler(
    commands=["status"]
)
def status(message):

    current_episode = data.get(
        "episode",
        1
    )

    current_quality = data.get(
        "quality",
        "480p"
    )

    bot.reply_to(
        message,
        f"""
<b>Current Settings</b>

Episode : {current_episode}

Quality :
{QUALITY_LIST.get(current_quality)}
"""
    )



# =========================
# QUALITY COMMAND
# =========================

@bot.message_handler(
    commands=["quality"]
)
def quality_menu(message):

    bot.reply_to(
        message,
        "Select Quality:",
        reply_markup=get_quality_buttons()
    )



# =========================
# QUALITY BUTTON HANDLER
# =========================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("quality_")
)
def quality_change(call):

    try:

        quality = call.data.replace(
            "quality_",
            ""
        )

        data["quality"] = quality

        save_data(data)


        bot.answer_callback_query(
            call.id,
            "Quality updated ✅"
        )


        bot.edit_message_text(
            f"""
<b>Quality Changed ✅</b>

New Quality:
{QUALITY_LIST[quality]}
""",
            call.message.chat.id,
            call.message.id
        )


    except Exception as e:

        logger.error(
            f"Quality error: {e}"
        )



# =========================
# RESTART COMMAND
# =========================

@bot.message_handler(
    commands=["restart"]
)
def restart(message):

    data["episode"] = 1
    data["quality"] = "480p"

    save_data(data)

    bot.reply_to(
        message,
        """
♻️ Counter Restarted

Episode : 1
Quality : 480p [SD]
"""
    )



# =========================
# NEXT EPISODE COMMAND
# =========================

@bot.message_handler(
    commands=["next"]
)
def next_episode(message):

    data["episode"] = data.get(
        "episode",
        1
    ) + 1

    save_data(data)


    bot.reply_to(
        message,
        f"""
Episode Updated ✅

Current Episode:
{data["episode"]}
"""
    )
# =========================
# FILE / VIDEO HANDLER
# =========================

@bot.message_handler(
    content_types=[
        "document",
        "video"
    ]
)
def handle_file(message):

    try:

        episode = data.get(
            "episode",
            1
        )

        quality_code = data.get(
            "quality",
            "480p"
        )

        quality = QUALITY_LIST.get(
            quality_code,
            "480p [SD]"
        )


        caption = create_caption(
            episode,
            quality
        )


        # DOCUMENT FILE
        if message.document:

            bot.send_document(
                message.chat.id,
                message.document.file_id,
                caption=caption
            )


        # VIDEO FILE
        elif message.video:

            bot.send_video(
                message.chat.id,
                message.video.file_id,
                caption=caption
            )


        # Increase episode after successful upload
        data["episode"] = episode + 1
        save_data(data)


        logger.info(
            f"File processed | Episode {episode} | {quality}"
        )


    except Exception as e:

        logger.error(
            f"File handler error: {e}"
        )

        bot.reply_to(
            message,
            "❌ Error while processing file"
        )



# =========================
# ERROR LOGGER
# =========================

@bot.message_handler(
    func=lambda message: True
)
def unknown(message):

    logger.info(
        f"Received message: {message.text}"
    )



# =========================
# TELEGRAM ERROR HANDLER
# =========================

def telegram_error():

    while True:

        try:

            time.sleep(10)

        except Exception as e:

            logger.error(
                f"Background error: {e}"
            )



# Start background thread

threading.Thread(
    target=telegram_error,
    daemon=True
).start()
# =========================
# START BOT
# =========================

def setup_webhook():

    try:

        logger.info(
            "Removing old webhook..."
        )

        bot.remove_webhook()


        time.sleep(1)


        webhook_url = (
            f"{WEBHOOK_URL}/{BOT_TOKEN}"
        )


        bot.set_webhook(
            url=webhook_url
        )


        logger.info(
            f"Webhook set: {webhook_url}"
        )


    except Exception as e:

        logger.error(
            f"Webhook setup error: {e}"
        )



# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":

    logger.info(
        "Starting Auto Caption Bot..."
    )


    setup_webhook()


    logger.info(
        f"Starting Flask on port {PORT}"
    )


    app.run(
        host="0.0.0.0",
        port=PORT
    )