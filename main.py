import asyncio
import os
from threading import Thread
import discord
from discord.ext import commands
import nest_asyncio
from flask import Flask
from telethon import TelegramClient
from telethon.sessions import StringSession

# Nest asyncio configuration
nest_asyncio.apply()

# --- Flask Server Setup ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running safely via StringSession!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)


# --- Configurations ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN")
API_ID = 33809887
API_HASH = "6d1b4c3acabca19425298ec275b0b469"
TARGET_TELEGRAM_BOT = "@FFPlayerInfoBot"

# Environment variables matching
STRING_SESSION = os.environ.get("TELEGRAM_STRING_SESSION", "")

if not STRING_SESSION:
    raise ValueError("ERROR: TELEGRAM_STRING_SESSION is missing in Render environment variables!")

# Setup Discord Bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Setup Telegram Client via StringSession
tg_client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)


@bot.event
async def on_ready():
    print(f"Logged in as Discord Bot: {bot.user}")
    if not tg_client.is_connected():
        await tg_client.start()
        print("Telegram Client Connected Successfully!")


@bot.command(name="get")
async def get_uid(ctx, uid: str):
    await ctx.send(f"⏳ **Processing UID:** `{uid}`... Request sent to Telegram Bot.")
    message_to_send = f"/get {uid}"

    try:
        async with tg_client.conversation(TARGET_TELEGRAM_BOT, timeout=60) as conv:
            await conv.send_message(message_to_send)
            
            # Count track korbo total koyta relevant content pelam
            # Target holo: 1ta Text info message, 1ta Sticker, 1ta Outfit Photo
            media_count = 0
            
            while True:
                try:
                    # Message ektar por ekta ashar jonno chotto 12 second individual waiting layer
                    response = await asyncio.wait_for(conv.get_response(), timeout=12)
                    
                    # 1. Skip processing text message ("Fetching information...")
                    if response.text and "Fetching information" in response.text:
                        continue
                    
                    # 2. Main Account Profile Details Card Text
                    if response.text and "Account Information:" in response.text:
                        await ctx.send(f"📢 **Telegram Bot Response:**\n\n{response.text}")
                        continue
                    
                    # 3. Handle Media Assets (Stickers + Images)
                    if response.media:
                        # Temporary local file save layer
                        file_path = await tg_client.download_media(response.media)
                        if file_path and os.path.exists(file_path):
                            await ctx.send(file=discord.File(file_path))
                            os.remove(file_path) # Storage clean
                            media_count += 1
                            
                        # Jodi text message ashar por already targeted media (sticker o photo) asha complete hoye jay, loop end korbo
                        if media_count >= 2:
                            break
                        continue
                        
                except asyncio.TimeoutError:
                    # Individual message asha theme gele nirgup break korbe, kono error string dekhabe na
                    break

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
