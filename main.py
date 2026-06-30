import asyncio
import os
from threading import Thread
import discord
from discord.ext import commands
import nest_asyncio
from flask import Flask
from telethon import TelegramClient

# Nest asyncio configuration
nest_asyncio.apply()

# --- Flask Server Setup ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running safely!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)


# --- Configurations ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN")
API_ID = 33809887
API_HASH = "6d1b4c3acabca19425298ec275b0b469"
TARGET_TELEGRAM_BOT = "@FFPlayerInfoBot"

# String session load
STRING_SESSION = os.environ.get("TELEGRAM_STRING_SESSION", "")

if not STRING_SESSION:
    raise ValueError("ERROR: TELEGRAM_STRING_SESSION is missing in Render environment variables!")

# Setup Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Setup Telegram Client via StringSession
from telethon.sessions import StringSession
tg_client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)


@bot.event
async def on_ready():
    print(f"Logged in as Discord Bot: {bot.user}")
    if not tg_client.is_connected():
        await tg_client.start()
        print("Telegram Client Connected Successfully!")


# --- Discord Command Block ---
@bot.command(name="get")
async def get_uid(ctx, uid: str):
    await ctx.send(f"⏳ **Processing UID:** `{uid}`... Requesting Telegram Bot asset pipeline.")
    message_to_send = f"/get {uid}"

    try:
        # 1. Telegram bot inbox e dynamic message text execute command push koro
        await tg_client.send_message(TARGET_TELEGRAM_BOT, message_to_send)
        
        # 2. TG bot processing executing target timeframe break context (5 second block wait)
        await asyncio.sleep(5)
        
        # 3. Last 4 message dump dynamic validation processing queue collect koro
        messages = await tg_client.get_messages(TARGET_TELEGRAM_BOT, limit=4)
        
        # Messages reverse direct read hobe jate chronological order order active thake
        for msg in reversed(messages):
            # A. Ignoring runtime standard notice stream lines
            if msg.text and "Fetching information" in msg.text:
                continue
                
            # B. Processing player data summary text card layout
            if msg.text and "Account Information:" in msg.text:
                await ctx.send(f"📢 **Telegram Bot Response:**\n\n{msg.text}")
                continue
                
            # C. Processing active visual media streams (Stickers and Image Summary assets)
            if msg.media:
                file_path = await tg_client.download_media(msg.media)
                if file_path and os.path.exists(file_path):
                    await ctx.send(file=discord.File(file_path))
                    os.remove(file_path) # Storage layer safe wipe
                    
    except Exception as e:
        await ctx.send(f"❌ **Error:** {str(e)}")


async def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    async with tg_client:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")
