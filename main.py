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
    return "Profile Finder Live!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
# ========================================================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==================== [ আপনার সেটিংস ] ====================
FINDER_CHANNEL_ID = 1520871063762768006        # প্রোফাইল ফাইন্ডার চ্যানেল আইডি

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
TELEGRAM_API_ID = 33809887          
TELEGRAM_API_HASH = "6d1b4c3acabca19425298ec275b0b469" 
TARGET_TELEGRAM_BOT = "@FFPlayerInfoBot" 
# ==========================================================

# সেশন ফাইলের নাম 'finder_tg_bridge' রাখা হলো
tg_client = TelegramClient('finder_tg_bridge', TELEGRAM_API_ID, TELEGRAM_API_HASH)

# লগইন স্টেটের গ্লোবাল ভেরিয়েবল
login_step = None 

@bot.event
async def on_ready():
    print(f'---------------------------------------------')
    print(f'Discord Bot {bot.user.name} হিসেবে রেডি!')
    print(f'---------------------------------------------')
    
    # ব্যাকগ্রাউন্ডে চেক করবে টেলিগ্রাম কানেক্টেড কি না
    if tg_client.is_connected():
        if await tg_client.is_user_authorized():
            print("টেলিগ্রাম ক্লায়েন্ট অলরেডি লগইন করা আছে!")
        else:
            print("⚠️ টেলিগ্রাম লগইন করা নেই! ডিসকোর্ডে /login কমান্ড দিন।")
    else:
        await tg_client.connect()
        if await tg_client.is_user_authorized():
            print("টেলিগ্রাম ক্লায়েন্ট সফলভাবে ব্যাকএন্ডে রানিং!")
        else:
            print("⚠️ টেলিগ্রাম লগইন করা নেই! ডিসকোর্ডে /login কমান্ড দিন।")

@bot.event
async def on_message(message):
    global login_step
    if message.author.bot:
        return

    raw_content = message.content.strip()
    bot_peer = TARGET_TELEGRAM_BOT.replace("@", "")

    # ==================== [ ডিসকোর্ড ওটিপি বাইপাস সিস্টেম ] ====================
    if message.channel.id == FINDER_CHANNEL_ID:
        # ১. লগইন শুরু করার কমান্ড
        if raw_content == "/login":
            if await tg_client.is_user_authorized():
                await message.reply("✅ টেলিগ্রাম অলরেডি সফলভাবে লগইন করা আছে! আর কিছু করতে হবে না।")
                return
            login_step = "phone"
            await message.reply("📱 দয়া করে আপনার টেলিগ্রাম অ্যাকাউন্টের **ফোন নম্বরটি** আন্তর্জাতিক ফরম্যাটে দিন।\n**উদাহরণ:** `/phone +8801XXXXXXXXX`")
            return

        # ২. ফোন নম্বর রিসিভ করা
        if raw_content.startswith("/phone") and login_step == "phone":
            parts = raw_content.split()
            if len(parts) < 2:
                await message.reply("❌ নম্বর ফরম্যাট ঠিক নেই। লিখুন: `/phone +8801XXXXXXXXX`")
                return
            phone_number = parts[1]
            await message.reply(f"📩 ফোন নম্বর `{phone_number}` এ ওটিপি (OTP) পাঠানো হচ্ছে... একটু অপেক্ষা করুন।")
            try:
                await tg_client.send_code_request(phone_number)
                login_step = f"otp:{phone_number}"
                await message.reply("🔑 আপনার টেলিগ্রামে একটি লগইন কোড গেছে। কোডটি এভাবে দিন:\n**উদাহরণ:** `/otp 12345`")
            except Exception as e:
                await message.reply(f"❌ কোড পাঠাতে সমস্যা হয়েছে: `{str(e)}` \nআবার চেষ্টা করতে `/login` লিখুন।")
                login_step = None
            return

        # ৩. ওটিপি কোড রিসিভ করে লগইন কমপ্লিট করা
        if raw_content.startswith("/otp") and login_step and login_step.startswith("otp:"):
            parts = raw_content.split()
            if len(parts) < 2:
                await message.reply("❌ কোড ফরম্যাট ঠিক নেই। লিখুন: `/otp 12345`")
                return
            otp_code = parts[1]
            phone_number = login_step.split(":")[1]
            try:
                await tg_client.sign_in(phone=phone_number, code=otp_code)
                await message.reply("🎉 **অভিনন্দন মারুফ ভাই!** টেলিগ্রাম ক্লায়েন্ট সফলভাবে লগইন হয়েছে এবং সেশন ফাইল তৈরি হয়েছে। এখন বটের সব ফিচার কাজ করবে!")
                login_step = None
            except Exception as e:
                await message.reply(f"❌ লগইন ব্যর্থ হয়েছে: `{str(e)}` \nআবার চেষ্টা করতে `/login` লিখুন।")
                login_step = None
            return

        # ==================== [ প্রোফাইল ফাইন্ডার কোর লজিক ] ====================
        if raw_content.lower().startswith("/uid"):
            if not await tg_client.is_user_authorized():
                await message.reply("⚠️ টেলিগ্রাম ক্লায়েন্ট লগইন করা নেই! দয়া করে প্রথমে ডিসকোর্ডে `/login` লিখে লগইন প্রসেস কমপ্লিট করুন।")
                return

            parts = raw_content.split()
            if len(parts) < 2 or not parts[1].isdigit():
                await message.reply("❌ ভুল ফরম্যাট! দয়া করে এভাবে লিখুন: `/uid 12345678`")
                return
            
            uid = parts[1]
            status_message = await message.reply(f"🔍 | **PROFILE FINDER** | {message.author.mention}, ফ্রিফায়ার UID: `{uid}` এর ফুল প্রোফাইল ও মিডিয়া টেলিগ্রাম থেকে আনা হচ্ছে...")

            @tg_client.on(events.NewMessage(from_users=bot_peer))
            async def handle_finder_media(event):
                if event.message.text and "fetching" not in event.message.text.lower():
                    embed = discord.Embed(
                        title=f"🎮 FREE FIRE PLAYER PROFILE",
                        description=event.message.text,
                        color=discord.Color.blurple()
                    )
                    await message.channel.send(embed=embed)
                
                if event.message.media:
                    path = await event.message.download_media()
                    if path:
                        await message.channel.send(file=discord.File(path))
                        if os.path.exists(path):
                            os.remove(path)

            try:
                print(f"DEBUG: Sending /get {uid} to {TARGET_TELEGRAM_BOT}")
                await tg_client.send_message(TARGET_TELEGRAM_BOT, f"/get {uid}")
                await asyncio.sleep(10)
                await status_message.delete()
                
            except Exception as e:
                await status_message.edit(content=f"❌ প্রোফাইল ডেটা আনতে সমস্যা হয়েছে: `{str(e)}`")
            finally:
                tg_client.remove_event_handler(handle_finder_media)

    await bot.process_commands(message)

async def main():
    if not DISCORD_BOT_TOKEN:
        print("❌ ERROR: কোনো বৈধ DISCORD_BOT_TOKEN পাওয়া যায়নি!")
        return
    
    keep_alive()
    print("Keep-alive Web server is active!")
    
    await tg_client.connect()
    await bot.start(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
