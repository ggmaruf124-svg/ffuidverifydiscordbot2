import os
import asyncio
import threading

import nest_asyncio
nest_asyncio.apply()

import discord
from discord.ext import commands
from telethon import TelegramClient
from telethon.sessions import StringSession
from flask import Flask

# --- Flask web worker ---
flask_app = Flask(__name__)

@flask_app.route("/")
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# --- Credentials ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is missing or blank.")

TELEGRAM_STRING_SESSION = os.environ.get("TELEGRAM_STRING_SESSION", "")
if not TELEGRAM_STRING_SESSION:
    raise ValueError("TELEGRAM_STRING_SESSION environment variable is missing or blank.")

API_ID = 33809887
API_HASH = "6d1b4c3acabca19425298ec275b0b469"
TARGET_BOT = "@FFPlayerInfoBot"

# --- Telegram client ---
tg_client = TelegramClient(StringSession(TELEGRAM_STRING_SESSION), API_ID, API_HASH)

# --- Discord bot ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.command(name="get")
async def get_uid(ctx, uid: str):
    await ctx.send(f"⏳ **Processing UID:** `{uid}`... Requesting Telegram Bot asset pipeline.")

    await tg_client.send_message(TARGET_BOT, f"/get {uid}")
    await asyncio.sleep(12)

    try:
        messages = await tg_client.get_messages(TARGET_BOT, limit=10)
    except Exception:
        return

    for msg in reversed(messages):
        try:
            # Skip messages we sent ourselves
            if msg.out:
                continue

            # Send text if present
            if msg.text and msg.text.strip():
                await ctx.send(f"📢 **Telegram Bot Response:**\n\n{msg.text}")

            # Send media if present
            if msg.media:
                file_path = await tg_client.download_media(msg.media)
                if file_path:
                    await ctx.send(file=discord.File(file_path))
                    os.remove(file_path)
        except Exception:
            continue

@bot.event
async def on_ready():
    print(f"Discord bot logged in as {bot.user}")

async def main():
    await tg_client.start()
    print("Telegram client started.")
    await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
