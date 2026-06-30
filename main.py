import os
import asyncio
import threading

import nest_asyncio
nest_asyncio.apply()

import discord
from discord.ext import commands
from telethon import TelegramClient, events
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
TARGET_BOT_USERNAME = "FFPlayerInfoBot"

# --- Telegram client ---
tg_client = TelegramClient(StringSession(TELEGRAM_STRING_SESSION), API_ID, API_HASH)

# --- Discord bot ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.command(name="get")
async def get_uid(ctx, uid: str):
    await ctx.send(f"⏳ **Processing UID:** `{uid}`... Requesting Telegram Bot asset pipeline.")

    # Collected messages from TG bot (message_id -> message object)
    collected = {}

    # Real-time listener: captures new messages from the TG bot
    @tg_client.on(events.NewMessage(from_users=TARGET_BOT_USERNAME))
    async def on_new_message(event):
        collected[event.message.id] = event.message

    # Real-time listener: captures edited messages (e.g. "Fetching..." -> full info)
    @tg_client.on(events.MessageEdited(from_users=TARGET_BOT_USERNAME))
    async def on_edited_message(event):
        collected[event.message.id] = event.message

    try:
        await tg_client.send_message(TARGET_BOT, f"/get {uid}")

        # Wait 12 seconds for the TG bot to finish sending everything
        await asyncio.sleep(12)

    finally:
        tg_client.remove_event_handler(on_new_message)
        tg_client.remove_event_handler(on_edited_message)

    if not collected:
        await ctx.send("⚠️ No response received from Telegram bot.")
        return

    # Send all collected messages to Discord in chronological order (oldest first)
    for msg in sorted(collected.values(), key=lambda m: m.id):
        try:
            if msg.text and msg.text.strip():
                await ctx.send(f"📢 **Telegram Bot Response:**\n\n{msg.text}")

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
