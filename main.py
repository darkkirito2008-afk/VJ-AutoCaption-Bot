import os
import json
import time
import logging

from threading import Thread

import telebot

from flask import Flask, request


# ==========================================
# LOGGING
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ==========================================
# CONFIG
# ==========================================

BOT_TOKEN = os.environ.get(
    "BOT_TOKEN"
)

WEBHOOK_URL = os.environ.get(
    "WEBHOOK_URL"
)

PORT = int(
    os.environ.get(
        "PORT",
        10000
    )
)


if not BOT_TOKEN:
    raise Exception(
        "BOT_TOKEN not found"
    )


bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


app = Flask(__name__)


# ==========================================
# QUALITY SETTINGS
# ==========================================

QUALITIES = [
    "480p [SD]",
    "720p [HD]",
    "1080p [FHD]"
]


# ==========================================
# STATE FILE
# ==========================================

STATE_FILE = "state.json"


DEFAULT_STATE = {
    "episode": 1,
    "quality_index": 0,
    "manual_quality": None
}



def load_state():

    try:

        if os.path.exists(
            STATE_FILE
        ):

            with open(
                STATE_FILE,
                "r"
            ) as f:

                return json.load(f)


    except Exception as e:

        logger.error(e)


    return DEFAULT_STATE.copy()



def save_state():

    try:

        with open(
            STATE_FILE,
            "w"
        ) as f:

            json.dump(
                state,
                f,
                indent=4
            )


        logger.info(
            f"Saved state: {state}"
        )


    except Exception as e:

        logger.error(e)



state = load_state()



# ==========================================
# FLASK WEBHOOK
# ==========================================

@app.route("/")
def home():

    return "✅ Auto Caption Bot Running"



@app.route(
    "/" + BOT_TOKEN,
    methods=["POST"]
)
def webhook():

    try:

        data = request.get_data().decode(
            "utf-8"
        )


        update = telebot.types.Update.de_json(
            data
        )


        bot.process_new_updates(
            [
                update
            ]
        )


        return "OK", 200


    except Exception as e:

        logger.exception(e)

        return "ERROR", 500



# ==========================================
# RUN FLASK
# ==========================================

def run_flask():

    logger.info(
        f"Starting Flask on port {PORT}"
    )


    app.run(
        host="0.0.0.0",
        port=PORT
    )
# ==========================================
# START BOT
# ==========================================

def start_bot():

    logger.info(
        "Starting Auto Caption Bot..."
    )


    # Remove old webhook

    try:

        bot.remove_webhook()

        logger.info(
            "Old webhook removed"
        )


    except Exception as e:

        logger.error(
            f"Webhook remove error: {e}"
        )


    time.sleep(2)



    # Set new webhook

    if WEBHOOK_URL:

        webhook = (
            WEBHOOK_URL.rstrip("/")
            +
            "/"
            +
            BOT_TOKEN
        )


        try:

            bot.set_webhook(
                url=webhook
            )


            logger.info(
                f"Webhook set: {webhook}"
            )


        except Exception as e:

            logger.exception(
                e
            )


    else:

        logger.warning(
            "WEBHOOK_URL missing"
        )



# ==========================================
# MAIN
# ==========================================
def media_handler(message):

if __name__ == "__main__":

    Thread(
        target=run_flask,
        daemon=True
    ).start()

    start_bot()

    logger.info(
        "Bot is running..."
    )

    while True:
        time.sleep(30)
# ==========================================
# START COMMAND
# ==========================================

@bot.message_handler(commands=["start"])
def start(message):

    bot.reply_to(
        message,
        """
✅ <b>Auto Caption Bot Ready</b>

Commands:

/setepisode - Change episode number
/setquality - Lock quality
/autoquality - Enable auto rotation
/status - Check current status
/restart - Reload state
"""
    )



# ==========================================
# STATUS COMMAND
# ==========================================

@bot.message_handler(commands=["status"])
def status(message):

    current_quality = (
        state["manual_quality"]
        if state["manual_quality"]
        else QUALITIES[state["quality_index"]]
    )


    bot.reply_to(
        message,
        f"""
📊 <b>Bot Status</b>

Episode :- {state['episode']}
🟡 Quality :- {current_quality}
"""
    )



# ==========================================
# SET EPISODE
# ==========================================

@bot.message_handler(commands=["setepisode"])
def set_episode(message):

    msg = bot.reply_to(
        message,
        "Send new episode number:"
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



# ==========================================
# QUALITY BUTTONS
# ==========================================

from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)



@bot.message_handler(commands=["setquality"])
def set_quality(message):

    markup = InlineKeyboardMarkup()


    for q in QUALITIES:

        markup.add(
            InlineKeyboardButton(
                q,
                callback_data=f"quality:{q}"
            )
        )


    bot.reply_to(
        message,
        "Select Quality:",
        reply_markup=markup
    )



@bot.callback_query_handler(
    func=lambda call: call.data.startswith("quality:")
)
def quality_callback(call):

    quality = call.data.split(
        ":"
    )[1]


    state["manual_quality"] = quality

    save_state()


    bot.answer_callback_query(
        call.id,
        "Quality locked"
    )


    bot.edit_message_text(
        f"✅ Quality set:\n{quality}",
        call.message.chat.id,
        call.message.message_id
    )



# ==========================================
# AUTO QUALITY
# ==========================================

@bot.message_handler(commands=["autoquality"])
def auto_quality(message):

    state["manual_quality"] = None

    save_state()


    bot.reply_to(
        message,
        "🔄 Auto quality rotation enabled"
    )



# ==========================================
# RESTART COMMAND
# ==========================================

@bot.message_handler(commands=["restart"])
def restart_bot(message):

    global state


    try:

        state = load_state()


        bot.reply_to(
            message,
            "♻️ Bot state refreshed"
        )


        logger.info(
            "State reloaded"
        )


    except Exception as e:

        logger.exception(e)


        bot.reply_to(
            message,
            f"❌ Restart error\n{e}"
        )
# ==========================================
# CAPTION GENERATOR
# ==========================================

def create_caption(quality):

    return f"""
Episode :- {state['episode']}
🗣 Language :- Hindi Dub
🟡 Quality :- {quality}
@NEW_ANIME_HINDI_DUB_OFFICIALL
"""


# ==========================================
# UPLOAD FUNCTION
# ==========================================

def upload_media(message):

    global state

    try:

        # Manual quality selected
        if state["manual_quality"]:

            quality = state["manual_quality"]


        # Auto rotate quality
        else:

            quality = QUALITIES[
                state["quality_index"]
            ]


        caption = create_caption(
            quality
        )


        if message.video:

            bot.send_video(
                message.chat.id,
                message.video.file_id,
                caption=caption
            )


        elif message.document:

            bot.send_document(
                message.chat.id,
                message.document.file_id,
                caption=caption
            )


        logger.info(
            f"Sent Episode {state['episode']} {quality}"
        )


        # ==============================
        # UPDATE AUTO ROTATION
        # ==============================

        if not state["manual_quality"]:

            state["quality_index"] += 1


            # After 3 qualities
            # move to next episode

            if state["quality_index"] >= len(QUALITIES):

                state["quality_index"] = 0

                state["episode"] += 1


        save_state()



    except Exception as e:

        logger.exception(e)


        bot.reply_to(
            message,
            f"❌ Upload Error\n{e}"
        )



# ==========================================
# MEDIA HANDLER
# ==========================================

@bot.message_handler(
    content_types=[
        "video",
        "document"
    ]
)
def media_handler(message):

    Thread(
        target=upload_media,
        args=(message,),
        daemon=True
    ).start()