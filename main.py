import asyncio
import os
from threading import Thread
import discord
from discord.ext import commands
import nest_asyncio
from flask import Flask
from telethon import TelegramClient, events

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

# String session configuration
STRING_SESSION = os.environ.get("TELEGRAM_STRING_SESSION", "")

if not STRING_SESSION:
    raise ValueError("ERROR: TELEGRAM_STRING_SESSION is missing in Render variables!")

# Setup Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Setup Telegram Client via StringSession
from telethon.sessions import StringSession
tg_client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# Active active tracking session management dictionary
active_requests = {}


# --- Telegram Message Listener Event ---
@tg_client.on(events.NewMessage(chats=TARGET_TELEGRAM_BOT))
async def handle_telegram_response(event):
    # Jodi text processing layout code runtime validation checks
    if event.text and "Fetching information" in event.text:
        return  # Completely ignore this initial spam message
        
    # Find active context to forward the text details or media
    for discord_ctx in list(active_requests.keys()):
        # 1. Profile Core text metadata forward
        if event.text and "Account Information:" in event.text:
            await discord_ctx.send(f"📢 **Telegram Bot Response:**\n\n{event.text}")
            
        # 2. Files forward handle (Sticker, Outfits Photo)
        elif event.media:
            file_path = await tg_client.download_media(event.media)
            if file_path and os.path.exists(file_path):
                await discord_ctx.send(file=discord.File(file_path))
                os.remove(file_path)


@bot.event
async def on_ready():
    print(f"Logged in as Discord Bot: {bot.user}")
    if not tg_client.is_connected():
        await tg_client.start()
        print("Telegram Client Connected Successfully!")


# --- Discord Command Setup ---
@bot.command(name="get")
async def get_uid(ctx, uid: str):
    await ctx.send(f"⏳ **Processing UID:** `{uid}`... Fetching dynamic profile asset package.")
    message_to_send = f"/get {uid}"

    # Target stream listener channel registry load
    active_requests[ctx] = True

    try:
        # Request trigger koro telegram bot-er inbox-e
        await tg_client.send_message(TARGET_TELEGRAM_BOT, message_to_send)
        
        # Max loop window runtime context processing hold 15 seconds
        # Jate data safely stream hobar por queue table clear hoy
        await asyncio.sleep(15)
        
    except Exception as e:
        await ctx.send(f"❌ **Error:** {str(e)}")
    finally:
        # Context cleanup registration table remove mapping
        if ctx in active_requests:
            del active_requests[ctx]


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
