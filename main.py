import os
import discord
from discord.ext import commands
import asyncio
from telethon import TelegramClient, events
from flask import Flask
from threading import Thread

# ==================== [ রেন্ডার পোর্ট বাইন্ডিং ফিক্স ] ====================
app = Flask('')

@app.route('/')
def home():
    return "Profile Finder Port Binding Successful!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """আলাদা থ্রেডে ফ্লাস্ক সার্ভার চালু করার ফাংশন"""
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
# ========================================================================

# ডিসকোর্ড বটের ইন্টেন্টস (Intents) সেটআপ
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==================== [ আপনার সেটিংস ] ====================
FINDER_CHANNEL_ID = 1520871063762768006        # প্রোফাইল ফাইন্ডার চ্যানেল আইডি

# রেন্ডারের Environment Variables থেকে ডিসকোর্ড টোকেন রিড করার লজিক
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# টেলিগ্রাম ক্লায়েন্ট সেটিংস
TELEGRAM_API_ID = 33809887          # আপনার টেলিগ্রাম API ID
TELEGRAM_API_HASH = "6d1b4c3acabca19425298ec275b0b469" 

# আপনার সচল টেলিগ্রাম বটের ইউজারনেম
TARGET_TELEGRAM_BOT = "@FFPlayerInfoBot" 
# ==========================================================

tg_client = TelegramClient('finder_tg_bridge', TELEGRAM_API_ID, TELEGRAM_API_HASH)

@bot.event
async def on_ready():
    print(f'---------------------------------------------')
    print(f'Profile Finder Bot {bot.user.name} হিসেবে রেডি!')
    print("টেলিগ্রাম ক্লায়েন্ট কানেক্ট করা হচ্ছে...")
    await tg_client.start()
    print("টেলিগ্রাম ক্লায়েন্ট সফলভাবে ব্যাকএন্ডে রানিং!")
    print(f'---------------------------------------------')

@bot.event
async def on_message(message):
    # বট নিজে মেসেজ দিলে বা নির্দিষ্ট চ্যানেল না হলে স্কিপ করবে
    if message.author.bot or message.channel.id != FINDER_CHANNEL_ID:
        return

    raw_content = message.content.strip()
    bot_peer = TARGET_TELEGRAM_BOT.replace("@", "")

    # ইউজার যদি প্রোফাইল খুঁজতে /uid ব্যবহার করে
    if raw_content.lower().startswith("/uid"):
        parts = raw_content.split()
        if len(parts) < 2 or not parts[1].isdigit():
            await message.reply("❌ ভুল ফরম্যাট! দয়া করে এভাবে লিখুন: `/uid 12345678`")
            return
        
        uid = parts[1]
        status_message = await message.reply(f"🔍 | **PROFILE FINDER** | {message.author.mention}, ফ্রিফায়ার UID: `{uid}` এর ফুল প্রোফাইল ও মিডিয়া টেলিগ্রাম থেকে আনা হচ্ছে... একটু অপেক্ষা করুন।")

        # টেলিগ্রাম থেকে আসা একাধিক মেসেজ/মিডিয়া ধরার জন্য ইভেন্ট হ্যান্ডলার
        @tg_client.on(events.NewMessage(from_users=bot_peer))
        async def handle_finder_media(event):
            # ১. যদি টেক্সট মেসেজ আসে
            if event.message.text and "fetching" not in event.message.text.lower():
                embed = discord.Embed(
                    title=f"🎮 FREE FIRE PLAYER PROFILE",
                    description=event.message.text,
                    color=discord.Color.blurple()
                )
                await message.channel.send(embed=embed)
            
            # ২. যদি ফটো, স্টিকার বা অন্য কোনো মিডিয়া ফাইল আসে
            if event.message.media:
                # ফাইলটি লোকালি ডাউনলোড করা
                path = await event.message.download_media()
                if path:
                    # ডিসকোর্ডে ফাইলটি সেন্ড করা
                    await message.channel.send(file=discord.File(path))
                    # পাঠানোর পর পিসি/সার্ভার থেকে ফাইলটি ডিলিট করে দেওয়া
                    if os.path.exists(path):
                        os.remove(path)

        try:
            print(f"DEBUG: Sending /get {uid} to {TARGET_TELEGRAM_BOT}")
            await tg_client.send_message(TARGET_TELEGRAM_BOT, f"/get {uid}")
            
            # টেলিগ্রাম বটকে ডেটা প্রসেস ও সব মিডিয়া পাঠানোর জন্য ১০ সেকেন্ড টাইম দেওয়া হলো
            await asyncio.sleep(10)
            await status_message.delete() # ওয়েটিং মেসেজটি ডিলিট করে দেওয়া
            
        except Exception as e:
            await status_message.edit(content=f"❌ প্রোফাইল ডেটা আনতে সমস্যা হয়েছে: `{str(e)}`")
        finally:
            tg_client.remove_event_handler(handle_finder_media)

    await bot.process_commands(message)

async def main():
    if not DISCORD_BOT_TOKEN:
        print("❌ ERROR: কোনো বৈধ DISCORD_BOT_TOKEN পাওয়া যায়নি! Environment Variables চেক করুন।")
        return
    
    # ব্যাকграাউন্ডে ফ্লাস্ক সার্ভার চালু করা হলো
    keep_alive()
    print("Keep-alive Web server is active!")

    async with tg_client:
        await bot.start(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
