import asyncio
import os
from threading import Thread
import discord
from discord.ext import commands
import nest_asyncio  # <--- Ekhon bamer extra space-ta thik kora hoyeche
from flask import Flask
from telethon import TelegramClient

# Nest asyncio config for conflict prevention
nest_asyncio.apply()

# --- Flask Server Setup (For Render Web Service) ---
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive and running!"


def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


# --- Bot & Telegram Configuration ---
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "YOUR_DISCORD_BOT_TOKEN_HERE")
API_ID = 33809887
API_HASH = "6d1b4c3acabca19425298ec275b0b469"
TARGET_TELEGRAM_BOT = "@FFPlayerInfoBot"

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)

# Telegram Client Setup
tg_client = TelegramClient("session_name", API_ID, API_HASH)


@bot.event
async def on_ready():
    print(f"Logged in as Discord Bot: {bot.user}")
    if not tg_client.is_connected():
        await tg_client.start()
        print("Telegram Client Connected Successfully!")


@bot.command(name="get")
async def get_uid(ctx, uid: str):
    await ctx.send(
        f"⏳ Processing UID: `{uid}`... Fetching details from Telegram."
    )
    message_to_send = f"/get {uid}"

    try:
        async with tg_client.conversation(TARGET_TELEGRAM_BOT, timeout=30) as conv:
            await conv.send_message(message_to_send)
            response = await conv.get_response()

            if response.text:
                await ctx.send(f"📢 **Telegram Bot Response:**\n\n{response.text}")
            else:
                await ctx.send("❌ Telegram bot raw text reply dey ni.")
    except asyncio.TimeoutError:
        await ctx.send("⏱️ Timeout! Telegram bot theke response paowa jayni.")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")


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
