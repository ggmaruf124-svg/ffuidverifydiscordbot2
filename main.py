import os
import asyncio
import threading
import discord
from discord.ext import commands
from telethon import TelegramClient, events
from flask import Flask

# ================= FLASK SERVER FOR RENDER =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running perfectly!"

def run_flask():
    # Render স্বয়ংক্রিয়ভাবে একটি PORT এসাইন করে, না পেলে default ৮০০০ ব্যবহার হবে
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

# ================= CONFIGURATION =================
TELEGRAM_API_ID = 33809887          
TELEGRAM_API_HASH = "6d1b4c3acabca19425298ec275b0b469"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_BOT = 'FFPlayerInfoBot' 
# =================================================

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())
tg_client = TelegramClient('my_account', TELEGRAM_API_ID, TELEGRAM_API_HASH)

@bot.event
async def on_ready():
    print(f"✅ Discord Bot is online as {bot.user}")
    
    if not tg_client.is_connected():
        await tg_client.connect()
    
    if await tg_client.is_user_authorized():
        print("✅ Telegram Account Session loaded successfully without OTP!")
    else:
        print("❌ ERROR: Session invalid! Please regenerate my_account.session file.")

@bot.command()
async def uid(ctx, uid_number: str):
    status_msg = await ctx.send(f"🔍 | **PROFILE FINDER** | {ctx.author.mention}, ফ্রিফায়ার UID: `{uid_number}` এর ফুল প্রোফাইল ও মিডিয়া টেলিগ্রাম থেকে আনা হচ্ছে...")
    
    if not tg_client.is_connected():
        await tg_client.connect()

    async def process_tg_message(event_msg):
        msg_text = event_msg.text or ""
        
        if "Fetching information for" in msg_text:
            return

        if "Account Information:" in msg_text:
            await ctx.send(f"```text\n{msg_text}\n```")
            
        elif event_msg.media:
            file_path = await tg_client.download_media(event_msg)
            if file_path:
                with open(file_path, "rb") as fh:
                    await ctx.send(file=discord.File(fh))
                try:
                    os.remove(file_path)
                except:
                    pass

    @tg_client.on(events.NewMessage(chats=TARGET_BOT))
    async def new_msg_handler(event):
        await process_tg_message(event.message)

    @tg_client.on(events.MessageEdited(chats=TARGET_BOT))
    async def edit_msg_handler(event):
        await process_tg_message(event.message)

    await tg_client.send_message(TARGET_BOT, f'/get {uid_number}')
    await asyncio.sleep(15)

    tg_client.remove_event_handler(new_msg_handler)
    tg_client.remove_event_handler(edit_msg_handler)

    try:
        await status_msg.delete()
    except:
        pass

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN missing in Environment Variables!")
    else:
        # Flask সার্ভারটিকে আলাদা একটি থ্রেডে ব্যাকগ্রাউন্ডে চালু করা হচ্ছে
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        # মূল ডিসকর্ড বট রান করা হচ্ছে
        bot.run(DISCORD_TOKEN)
