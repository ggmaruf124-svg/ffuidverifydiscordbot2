import os
import asyncio
import threading
import discord
from discord.ext import commands
from telethon import TelegramClient
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

    # ১. টেলিগ্রাম বটের কাছে রিকোয়েস্ট পাঠানো
    await tg_client.send_message(TARGET_BOT, f'/get {uid_number}')
    
    # ফ্রিফায়ার বটটি যেন ডাটা জেনারেট করার সময় পায় সেজন্য ৫ সেকেন্ড অপেক্ষা
    await asyncio.sleep(5)

    # ২. সরাসরি চ্যাট হিস্ট্রি থেকে শেষ ৫টি মেসেজ টেনে আনা (কোনো ইভেন্ট লিসেনার লাগবে না)
    messages_to_forward = []
    async for message in tg_client.iter_messages(TARGET_BOT, limit=5):
        msg_text = message.text or ""
        
        # 'Fetching information' মেসেজটি বাদ দেওয়া
        if "Fetching information for" in msg_text:
            continue
            
        messages_to_forward.append(message)

    # মেসেজগুলো যেহেতু উল্টো ক্রমানুসারে আসে (নতুন থেকে পুরোনো), তাই এটাকে সোজা করে নেওয়া
    messages_to_forward.reverse()

    # ৩. ডিসকর্ডে ফরওয়ার্ড করা শুরু
    if not messages_to_forward:
        await ctx.send("⚠️ টেলিগ্রাম বট থেকে কোনো রেসপন্স পাওয়া যায়নি! ফ্রিফায়ার বটটি হয়তো ডাউন আছে।")
    else:
        for msg in messages_to_forward:
            # টেক্সট ডাটা পাঠানো
            if msg.text and "Account Information:" in msg.text:
                await ctx.send(f"```text\n{msg.text}\n```")
                await asyncio.sleep(1)
                
            # স্টিকার বা ফটো পাঠানো
            elif msg.media:
                try:
                    file_path = await tg_client.download_media(msg)
                    if file_path and os.path.exists(file_path):
                        await ctx.send(file=discord.File(file_path))
                        await asyncio.sleep(1)
                        os.remove(file_path)
                except Exception as e:
                    print(f"Media forward error: {e}")

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
