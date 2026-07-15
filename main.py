import os
import json
import time
import logging
from threading import Thread

from flask import Flask, request
import telebot
from telebot.types import Update


# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

logger.info("Starting Auto Caption Bot...")


# ==================================================
# CONFIG
# ==================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN missing in Render Environment")

PORT = int(os.environ.get("PORT", 10000))

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")


bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


app = Flask(__name__)


# ==================================================
# STATE STORAGE
# ==================================================

STATE_FILE = "state.json"


DEFAULT_STATE = {
    "episode": 1,
    "quality_index": 0,
    "manual_quality": None
}


def save_state():

    try:
        with open(STATE_FILE, "w") as file:
            json.dump(
                state,
                file,
                indent=4
            )

    except Exception as e:
        logger.error(
            f"State save error: {e}"
        )


def load_state():

    if not os.path.exists(STATE_FILE):

        with open(STATE_FILE, "w") as file:
            json.dump(
                DEFAULT_STATE,
                file,
                indent=4
            )

        return DEFAULT_STATE.copy()


    try:

        with open(STATE_FILE, "r") as file:
            return json.load(file)

    except Exception as e:

        logger.error(
            f"State load error: {e}"
        )

        return DEFAULT_STATE.copy()



state = load_state()


# ==================================================
# QUALITY LIST
# ==================================================

QUALITIES = [
    "480p [SD]",
    "720p [HD]",
    "1080p [FHD]"
]


# ==================================================
# FLASK WEBHOOK
# ==================================================

@app.route("/")
def home():

    return "✅ Auto Caption Bot Alive"


@app.route(
    "/" + BOT_TOKEN,
    methods=["POST"]
)
def webhook():

    try:

        json_string = request.get_data().decode(
            "utf-8"
        )

        update = Update.de_json(
            json_string
        )

        bot.process_new_updates(
            [update]
        )

        return "OK", 200


    except Exception as e:

        logger.exception(e)

        return "ERROR", 500



# ==================================================
# RUN FLASK
# ==================================================

def run_flask():

    logger.info(
        f"Starting Flask on port {PORT}"
    )

    app.run(
        host="0.0.0.0",
        port=PORT
    )
# ==================================================
# START COMMAND
# ==================================================

@bot.message_handler(commands=["start"])
def start(message):

    bot.reply_to(
        message,
        """
🤖 <b>Auto Caption Bot</b>

Commands:

/setepisode - Change episode number
/setquality - Select quality
/autoquality - Enable auto rotation
/status - Check status
        """
    )


# ==================================================
# STATUS
# ==================================================

@bot.message_handler(commands=["status"])
def status(message):

    if state["manual_quality"]:

        quality = state["manual_quality"]

    else:

        quality = (
            QUALITIES[
                state["quality_index"]
            ]
            + " (Auto)"
        )


    bot.reply_to(
        message,
        f"""
📺 <b>Status</b>

Episode : {state["episode"]}
Quality : {quality}
        """
    )


# ==================================================
# SET EPISODE
# ==================================================

@bot.message_handler(commands=["setepisode"])
def set_episode(message):

    msg = bot.reply_to(
        message,
        "Send episode number:"
    )

    bot.register_next_step_handler(
        msg,
        save_episode
    )


def save_episode(message):

    try:

        state["episode"] = int(
            message.text
        )

        state["quality_index"] = 0

        save_state()


        bot.reply_to(
            message,
            f"✅ Episode changed to {state['episode']}"
        )


    except:

        bot.reply_to(
            message,
            "❌ Invalid episode number"
        )


# ==================================================
# QUALITY BUTTONS
# ==================================================

@bot.message_handler(commands=["setquality"])
def set_quality(message):

    markup = InlineKeyboardMarkup(
        row_width=1
    )


    for quality in QUALITIES:

        markup.add(
            InlineKeyboardButton(
                text=quality,
                callback_data=f"quality_{quality}"
            )
        )


    markup.add(
        InlineKeyboardButton(
            "🔄 Auto Quality",
            callback_data="auto_quality"
        )
    )


    bot.reply_to(
        message,
        "Select Quality:",
        reply_markup=markup
    )


# ==================================================
# CALLBACK BUTTON HANDLER
# ==================================================

@bot.callback_query_handler(
    func=lambda call: True
)
def callback_handler(call):


    if call.data.startswith(
        "quality_"
    ):

        quality = call.data.replace(
            "quality_",
            ""
        )


        state["manual_quality"] = quality

        save_state()


        bot.answer_callback_query(
            call.id,
            "Quality locked"
        )


        bot.edit_message_text(
            f"✅ Quality set to:\n{quality}",
            call.message.chat.id,
            call.message.message_id
        )


    elif call.data == "auto_quality":


        state["manual_quality"] = None

        save_state()


        bot.answer_callback_query(
            call.id,
            "Auto rotation enabled"
        )


        bot.edit_message_text(
            "✅ Auto quality rotation enabled",
            call.message.chat.id,
            call.message.message_id
        )


# ==================================================
# AUTO QUALITY COMMAND
# ==================================================

@bot.message_handler(commands=["autoquality"])
def auto_quality(message):

    state["manual_quality"] = None

    save_state()


    bot.reply_to(
        message,
        "✅ Auto quality rotation enabled"
    )
# ==================================================
# UPLOAD FUNCTION
# ==================================================

def upload_file(message):

    try:

        # Select quality
        if state["manual_quality"]:

            quality = state["manual_quality"]

        else:

            quality = QUALITIES[
                state["quality_index"]
            ]


        caption = (
            f"Episode :- {state['episode']}\n"
            f"🗣 Language :- Hindi Dub\n"
            f"🟡 Quality :- {quality}\n"
            f"@NEW_ANIME_HINDI_DUB_OFFICIALL"
        )


        # Send video

        if message.video:

            bot.send_video(
                chat_id=message.chat.id,
                video=message.video.file_id,
                caption=caption
            )


        # Send document

        elif message.document:

            bot.send_document(
                chat_id=message.chat.id,
                document=message.document.file_id,
                caption=caption
            )


        # Auto rotation

        if state["manual_quality"] is None:


            state["quality_index"] += 1


            # After 480 + 720 + 1080
            # move to next episode

            if state["quality_index"] >= 3:

                state["quality_index"] = 0

                state["episode"] += 1


            save_state()


        logger.info(
    f"CURRENT STATE: Episode={state['episode']} QualityIndex={state['quality_index']} Selected={quality}"
)

        bot.reply_to(
            message,
            f"❌ Upload Error\n{e}"
        )



# ==================================================
# MEDIA HANDLER
# ==================================================

@bot.message_handler(
    content_types=[
        "video",
        "document"
    ]
)
def media_handler(message):

    Thread(
        target=upload_file,
        args=(message,),
        daemon=True
    ).start()



# ==================================================
# RENDER START
# ==================================================

if __name__ == "__main__":


    # Start Flask server

    Thread(
        target=run_flask,
        daemon=True
    ).start()


    time.sleep(3)


    try:

        logger.info(
            "Removing old webhook..."
        )

        bot.remove_webhook()


        time.sleep(2)


        if WEBHOOK_URL:

            webhook_url = (
                WEBHOOK_URL.rstrip("/")
                + "/"
                + BOT_TOKEN
            )


            logger.info(
                f"Setting webhook: {webhook_url}"
            )


            bot.set_webhook(
                url=webhook_url
            )


        logger.info(
            "✅ Bot Started Successfully"
        )


    except Exception as e:

        logger.exception(e)



    # Keep Render process alive

    while True:

        time.sleep(30)