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
        print("✅ Telegram Account Session loaded successfully!")
    else:
        print("❌ ERROR: Session invalid!")

@bot.command()
async def uid(ctx, uid_number: str):
    # ডিসকর্ডে লোডিং মেসেজ পাঠানো
    status_msg = await ctx.send(f"🔍 | **PROFILE FINDER** | {ctx.author.mention}, ফ্রিফায়ার UID: `{uid_number}` এর ফুল প্রোফাইল ও মিডিয়া টেলিগ্রাম থেকে আনা হচ্ছে...")
    
    if not tg_client.is_connected():
        await tg_client.connect()

    # একটি ইভেন্ট কন্ট্রোলার যা ৩টি প্রয়োজনীয় মেসেজ পেলে লুপ থামিয়ে দেবে
    loop_control = asyncio.Event()
    received_count = 0

    @tg_client.on(events.NewMessage(chats=TARGET_BOT))
    async def new_msg_handler(event):
        nonlocal received_count
        msg_text = event.message.text or ""
        
        # ১. প্রথম মেসেজ (Fetching...) আসলে সেটাকে সরাসরি ইগনোর করবে
        if "Fetching information for" in msg_text:
            return

        # ২. মূল অ্যাকাউন্ট ইনফরমেশন টেক্সট আসলে ডিসকর্ডে পাঠাবে
        if "Account Information:" in msg_text:
            await ctx.send(f"```text\n{msg_text}\n```")
            received_count += 1
            
        # ৩. স্টিকার বা ইমেজ (মিডিয়া) আসলে সাথে সাথে ডাউনলোড করে ডিসকর্ডে পাঠিয়ে দেবে
        elif event.message.media:
            file_path = await tg_client.download_media(event.message)
            if file_path:
                with open(file_path, "rb") as fh:
                    await ctx.send(file=discord.File(fh))
                try:
                    os.remove(file_path)
                except:
                    pass
            received_count += 1

        # যখনই লোডিং বাদে বাকি ৩টি মেসেজ (টেক্সট, স্টিকার, ফটো) পাঠানো শেষ হবে
        if received_count >= 3:
            loop_control.set()

    # টেলিগ্রাম বটের কাছে কমান্ড পাঠানো হলো
    await tg_client.send_message(TARGET_BOT, f'/get {uid_number}')

    try:
        # সর্বোচ্চ ২৫ সেকেন্ড অপেক্ষা করবে সব ডাটা লাইভ প্রসেস হওয়ার জন্য
        await asyncio.wait_for(loop_control.wait(), timeout=25.0)
    except asyncio.TimeoutError:
        print("টাইমআউট! নির্দিষ্ট সময়ে সব মিডিয়া আসেনি।")

    # ইভেন্ট হ্যান্ডলার রিমুভ করা (যাতে পরবর্তী কমান্ডে জ্যাম না লাগে)
    tg_client.remove_event_handler(new_msg_handler)

    # ডিসকর্ডের লোডিং মেসেজটি ডিলিট করে দেওয়া
    try:
        await status_msg.delete()
    except:
        pass

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN missing!")
    else:
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        bot.run(DISCORD_TOKEN)
