import os
import asyncio
import threading
import logging

import nest_asyncio
nest_asyncio.apply()

import discord
from discord.ext import commands
from telethon import TelegramClient
from telethon.sessions import StringSession
from flask import Flask

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("bridge-bot")

# ── Credentials & Config ───────────────────────────────────────────────────────
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("Missing environment variable: DISCORD_TOKEN")

TG_API_ID   = 33809887
TG_API_HASH = "6d1b4c3acabca19425298ec275b0b469"

TG_STRING_SESSION = os.environ.get("TELEGRAM_STRING_SESSION", "")
if not TG_STRING_SESSION:
    raise ValueError(
        "Missing environment variable: TELEGRAM_STRING_SESSION. "
        "Generate one with Telethon's StringSession and set it before deploying."
    )

TARGET_BOT = "@FFPlayerInfoBot"
PORT       = int(os.environ.get("PORT", 10000))

# ── Flask keep-alive web worker ────────────────────────────────────────────────
flask_app = Flask(__name__)

@flask_app.route("/")
def health():
    return {"status": "ok", "service": "discord-telegram-bridge"}, 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=PORT, use_reloader=False, debug=False)

def start_flask_daemon():
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    log.info("Flask keep-alive server started on port %s", PORT)

# ── Telegram client ────────────────────────────────────────────────────────────
tg_client = TelegramClient(
    StringSession(TG_STRING_SESSION),
    TG_API_ID,
    TG_API_HASH,
)

# ── Discord bot ────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# ── Discord events ─────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    log.info("Discord bot online as %s (id=%s)", bot.user, bot.user.id)

# ── /get command ───────────────────────────────────────────────────────────────
@bot.command(name="get")
async def get_player(ctx, uid: str):
    """
    Usage: /get <uid>
    Fetches Free Fire player info from @FFPlayerInfoBot via Telegram
    and relays text + media assets back to this Discord channel.
    """
    await ctx.send(
        f"⏳ **Processing UID:** `{uid}`... Requesting Telegram Bot asset pipeline."
    )
    log.info("Received /get request for UID=%s from Discord user %s", uid, ctx.author)

    try:
        # 1. Forward command to the target Telegram bot
        await tg_client.send_message(TARGET_BOT, f"/get {uid}")
        log.info("Forwarded /get %s to %s", uid, TARGET_BOT)

        # 2. Give the external bot time to process and reply
        await asyncio.sleep(5)

        # 3. Fetch the last 4 messages from the conversation
        messages = await tg_client.get_messages(TARGET_BOT, limit=4)

        if not messages:
            log.info("No messages returned from %s — aborting silently.", TARGET_BOT)
            return

        # 4. Process in chronological order (oldest → newest)
        for msg in reversed(messages):

            # ── Condition A: Ignore noise ──────────────────────────────────────
            if msg.text and "Fetching information" in msg.text:
                log.debug("Skipping noise message: %s", msg.text[:60])
                continue

            # ── Condition B: Capture profile text data ─────────────────────────
            if msg.text and "Account Information:" in msg.text:
                await ctx.send(f"📢 **Telegram Bot Response:**\n\n{msg.text}")
                log.info("Sent account information text to Discord.")
                continue

            # ── Condition C: Capture media assets (images / stickers) ──────────
            if msg.media:
                file_path = None
                try:
                    file_path = await tg_client.download_media(msg.media)
                    if file_path and os.path.exists(file_path):
                        await ctx.send(file=discord.File(file_path))
                        log.info("Sent media asset to Discord: %s", file_path)
                    else:
                        log.warning("Media download returned no file — skipping.")
                except Exception as media_err:
                    log.error("Failed to download/send media: %s", media_err)
                finally:
                    # Always clean up the local temp file
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                        log.debug("Cleaned up temp file: %s", file_path)
                continue

    except Exception as err:
        # Silently log — do not spam Discord channel with error frames
        log.error("Error during Telegram fetch pipeline for UID=%s: %s", uid, err)

# ── Entry point ────────────────────────────────────────────────────────────────
async def main():
    # Start Flask daemon before connecting any async clients
    start_flask_daemon()

    # Connect Telegram client
    await tg_client.start()
    log.info("Telegram client authenticated and connected.")

    # Start Discord bot (blocks until stopped)
    try:
        await bot.start(DISCORD_TOKEN)
    finally:
        if tg_client.is_connected():
            await tg_client.disconnect()
            log.info("Telegram client disconnected cleanly.")

if __name__ == "__main__":
    asyncio.run(main())
