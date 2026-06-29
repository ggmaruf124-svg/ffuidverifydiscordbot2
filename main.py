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
    status_msg = await ctx.send(f"🔍 | **PROFILE FINDER** | {ctx.author.mention}, ফ্রিফায়ার UID: `{uid_number}` এর ফুল প্রোফাইল ও মিডিয়া টেলিগ্রাম থেকে আনা হচ্ছে...")
    
    if not tg_client.is_connected():
        await tg_client.connect()

    # টেলিগ্রাম থেকে আসা মেসেজগুলো প্রসেস করার ফাংশন
    async def process_tg_message(event_msg):
        msg_text = event_msg.text or ""
        
        # ১. প্রথম লোডিং মেসেজ আসলে সেটাকে ইগনোর করবে
        if "Fetching information for" in msg_text:
            return

        # ২. মূল অ্যাকাউন্ট ইনফরমেশন টেক্সট ডিসকর্ডে পাঠানো
        if "Account Information:" in msg_text:
            await ctx.send(f"```text\n{msg_text}\n```")
            await asyncio.sleep(1) # ডিসকর্ড রেট-লিমিট এড়াতে ১ সেকেন্ড বিরতি
            
        # ৩. স্টিকার বা ইমেজ (মিডিয়া) আসলে ডাউনলোড করে পাঠানো
        elif event_msg.media:
            try:
                file_path = await tg_client.download_media(event_msg)
                if file_path and os.path.exists(file_path):
                    await ctx.send(file=discord.File(file_path))
                    await asyncio.sleep(1)
                    os.remove(file_path)
            except Exception as e:
                print(f"Media forward error: {e}")

    # নতুন মেসেজ শোনার লিসেনার
    @tg_client.on(events.NewMessage(chats=TARGET_BOT))
    async def new_msg_handler(event):
        await process_tg_message(event.message)

    # টেলিগ্রাম বটের কাছে রিকোয়েস্ট পাঠানো
    await tg_client.send_message(TARGET_BOT, f'/get {uid_number}')

    # টেলিগ্রাম বটকে ডাটা পাঠানোর জন্য ২০ সেকেন্ড সময় দেওয়া হলো
    # এই ২০ সেকেন্ডের মধ্যে আসা সব মেসেজ (লোডিং বাদে) ডিসকর্ডে ফরওয়ার্ড হবে
    await asyncio.sleep(20)

    # কাজ শেষ হলে লিসেনার বন্ধ করা
    tg_client.remove_event_handler(new_msg_handler)

    # ডিসকর্ডের লোডিং স্ট্যাটাস মেসেজটি ডিলিট করা
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
