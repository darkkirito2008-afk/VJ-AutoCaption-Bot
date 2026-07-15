import os
import json
import time
import logging
from threading import Thread

from flask import Flask, request
import telebot
from telebot.types import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# ==========================================================
# LOGGING
# ==========================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

logger.info("Starting Auto Caption Bot...")

# ==========================================================
# CONFIG
# ==========================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

STATE_FILE = "state.json"

# ==========================================================
# LOAD / SAVE STATE
# ==========================================================

DEFAULT_STATE = {
    "episode": 1,
    "quality_index": 0,
    "manual_quality": None
}


def load_state():
    if not os.path.exists(STATE_FILE):
        save_state(DEFAULT_STATE)
        return DEFAULT_STATE.copy()

    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed loading state: {e}")
        save_state(DEFAULT_STATE)
        return DEFAULT_STATE.copy()


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


state = load_state()

QUALITIES = [
    "480p [SD]",
    "720p [HD]",
    "1080p [FHD]"
]

# ==========================================================
# FLASK
# ==========================================================

@app.route("/")
def home():
    return "✅ Auto Caption Bot Running"


@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    try:
        update = Update.de_json(
            request.get_data().decode("utf-8")
        )

        bot.process_new_updates([update])

        return "OK", 200

    except Exception as e:
        logger.exception(e)
        return "ERROR", 500


# ==========================================================
# START WEB SERVER
# ==========================================================

def run_web():
    logger.info(f"Running Flask on port {PORT}")

    app.run(
        host="0.0.0.0",
        port=PORT
    )
# ==========================================================
# COMMANDS
# ==========================================================

@bot.message_handler(commands=["start"])
def start(message):
    text = (
        "🤖 <b>Auto Caption Bot</b>\n\n"
        "Available Commands:\n"
        "/setepisode - Set episode number\n"
        "/setquality - Lock quality\n"
        "/autoquality - Enable auto rotation\n"
        "/status - Show current status"
    )

    bot.reply_to(message, text, parse_mode="HTML")


@bot.message_handler(commands=["status"])
def status(message):
    quality = (
        state["manual_quality"]
        if state["manual_quality"]
        else "Auto Rotate"
    )

    bot.reply_to(
        message,
        f"📺 Episode : {state['episode']}\n"
        f"🎞 Quality : {quality}"
    )


# ==========================================================
# SET EPISODE
# ==========================================================

@bot.message_handler(commands=["setepisode"])
def set_episode(message):
    msg = bot.reply_to(
        message,
        "Send the new episode number:"
    )

    bot.register_next_step_handler(
        msg,
        save_episode
    )


def save_episode(message):
    try:
        episode = int(message.text)

        state["episode"] = episode
        save_state(state)

        bot.reply_to(
            message,
            f"✅ Episode set to {episode}"
        )

    except ValueError:
        bot.reply_to(
            message,
            "❌ Please send a valid number."
        )


# ==========================================================
# QUALITY MENU
# ==========================================================

@bot.message_handler(commands=["setquality"])
def set_quality(message):

    markup = InlineKeyboardMarkup(row_width=1)

    for q in QUALITIES:
        markup.add(
            InlineKeyboardButton(
                q,
                callback_data=f"quality:{q}"
            )
        )

    bot.reply_to(
        message,
        "Choose a quality:",
        reply_markup=markup
    )


@bot.message_handler(commands=["autoquality"])
def auto_quality(message):

    state["manual_quality"] = None
    save_state(state)

    bot.reply_to(
        message,
        "✅ Auto quality rotation enabled."
    )


# ==========================================================
# CALLBACKS
# ==========================================================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):

    if call.data.startswith("quality:"):

        quality = call.data.split(":", 1)[1]

        state["manual_quality"] = quality
        save_state(state)

        bot.answer_callback_query(
            call.id,
            f"Locked to {quality}"
        )

        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )

        bot.send_message(
            call.message.chat.id,
            f"✅ Quality locked to:\n{quality}"
        )
# ==========================================================
# UPLOAD
# ==========================================================

def upload(message):
    try:

        if state["manual_quality"]:
            quality = state["manual_quality"]

        else:
            quality = QUALITIES[state["quality_index"]]

        caption = (
            f"Episode :- {state['episode']}\n"
            f"🗣 Language :- Hindi Dub\n"
            f"🟡 Quality :- {quality}\n"
            f"@NEW_ANIME_HINDI_DUB_OFFICIALL"
        )

        if message.content_type == "video":

            bot.send_video(
                chat_id=message.chat.id,
                video=message.video.file_id,
                caption=caption
            )

        elif message.content_type == "document":

            bot.send_document(
                chat_id=message.chat.id,
                document=message.document.file_id,
                caption=caption
            )

        # Auto rotation
        if state["manual_quality"] is None:

            state["quality_index"] += 1

            if state["quality_index"] >= len(QUALITIES):
                state["quality_index"] = 0
                state["episode"] += 1

            save_state(state)

        logger.info(
            f"Uploaded Episode {state['episode']} | {quality}"
        )

    except Exception as e:
        logger.exception(e)

        bot.reply_to(
            message,
            f"❌ Upload Failed\n\n{e}"
        )


# ==========================================================
# MEDIA HANDLER
# ==========================================================

@bot.message_handler(content_types=["video", "document"])
def media(message):
    Thread(
        target=upload,
        args=(message,),
        daemon=True
    ).start()


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    Thread(
        target=run_web,
        daemon=True
    ).start()

    time.sleep(2)

    try:

        logger.info("Removing old webhook...")

        bot.remove_webhook()

        time.sleep(2)

        if WEBHOOK_URL:

            logger.info(f"Setting webhook: {WEBHOOK_URL}")

            bot.set_webhook(
                url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
            )

        logger.info("✅ Bot Started Successfully")

    except Exception as e:
        logger.exception(e)

    while True:
        time.sleep(30)