import os
import asyncio
import discord
from discord.ext import commands
from telethon import TelegramClient, events

# ================= CONFIGURATION =================
# আপনার দেওয়া টেলিগ্রাম API ডিটেইলস সরাসরি বসানো হয়েছে
TELEGRAM_API_ID = 33809887          
TELEGRAM_API_HASH = "6d1b4c3acabca19425298ec275b0b469"

# ডিসকর্ড টোকেন রেন্ডারের Environment Variable থেকে আসবে (সেফটি পারপাস)
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# যে টেলিগ্রাম বট থেকে ফ্রিফায়ার প্রোফাইল ডাটা আনা হচ্ছে তার ইউজারনেম (@ ছাড়া)
TARGET_BOT = '@FFPlayerInfoBot' 
# =================================================

# ডিসকর্ড ও টেলিগ্রাম ক্লায়েন্ট ইনিশিয়েট করা
bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())
tg_client = TelegramClient('session_name', TELEGRAM_API_ID, TELEGRAM_API_HASH)

@bot.event
async def on_ready():
    print(f"✅ Discord Bot is online as {bot.user}")
    # ডিসকর্ড বট রান হওয়ার সাথে সাথে ব্যাকগ্রাউন্ডে টেলিগ্রাম ক্লায়েন্ট স্টার্ট করা
    if not tg_client.is_connected():
        await tg_client.start()
    print("✅ Telegram Client is connected and authenticated.")

@bot.command()
async def uid(ctx, uid_number: str):
    # ডিসকর্ডে লোডিং বা ইনিশিয়াল রেসপন্স পাঠানো
    status_msg = await ctx.send(f"🔍 | **PROFILE FINDER** | {ctx.author.mention}, ফ্রিফায়ার UID: `{uid_number}` এর ফুল প্রোফাইল ও মিডিয়া টেলিগ্রাম থেকে আনা হচ্ছে...")
    
    # টেলিগ্রাম ক্লায়েন্ট কানেকশন সেফটি চেক
    if not tg_client.is_connected():
        await tg_client.connect()

    received_messages = []
    loop_control = asyncio.Event()

    # টেলিগ্রাম ইভেন্ট হ্যান্ডলার: নতুন মেসেজ আসা বা আগের মেসেজ এডিট হওয়া ট্র্যাক করবে
    @tg_client.on(events.NewMessage(chats=TARGET_BOT))
    @tg_client.on(events.MessageEdited(chats=TARGET_BOT))
    async def handler(event):
        msg_text = event.message.text or ""
        
        # ১. প্রথম লোডিং মেসেজটা ইগনোর করার ফিল্টার
        if "Fetching information for" in msg_text:
            return

        # ২. মূল অ্যাকাউন্ট ইনফরমেশন টেক্সট ক্যাচ করা
        if "Account Information:" in msg_text and event.message.id not in [m.id for m in received_messages]:
            received_messages.append(event.message)
            
        # ৩. স্টিকার বা ইমেজ (মিডিয়া) ক্যাচ করা
        elif event.message.media and event.message.id not in [m.id for m in received_messages]:
            received_messages.append(event.message)

        # আমাদের ৩টি জিনিস লাগবে: মূল টেক্সট, স্টিকার, এবং আউটফিট ইমেজ (image.png)
        if len(received_messages) >= 3:
            loop_control.set()

    # টেলিগ্রাম বটের কাছে কমান্ড পাঠানো
    await tg_client.send_message(TARGET_BOT, f'/get {uid_number}')

    try:
        # সর্বোচ্চ ২৫ সেকেন্ড অপেক্ষা করবে সব ডাটা সিরিয়ালি আসার জন্য
        await asyncio.wait_for(loop_control.wait(), timeout=25.0)
    except asyncio.TimeoutError:
        print("টাইমআউট! সব মেসেজ নির্দিষ্ট সময়ে আসেনি, যা পাওয়া গেছে তাই পাঠানো হচ্ছে...")

    # ইভেন্ট হ্যান্ডলার রিমুভ করা যাতে পরের কমান্ডের সাথে ওভারল্যাপ না হয়
    tg_client.remove_event_handler(handler)

    # যদি টেলিগ্রাম থেকে কোনো ডাটাই না আসে
    if not received_messages:
        await ctx.send("❌ টেলিগ্রাম বট থেকে কোনো রেসপন্স পাওয়া যায়নি। অনুগ্রহ করে আবার চেষ্টা করুন।")
        return

    # ডিসকর্ডের প্রথম লোডিং মেসেজটা ডিলিট করে ক্লিন করা
    try:
        await status_msg.delete()
    except:
        pass

    # সংগৃহীত মেসেজগুলো সিরিয়ালি ডিসকর্ডে ফরওয়ার্ড করা
    for tg_msg in received_messages:
        # যদি টেক্সট মেসেজ হয় (Account Information)
        if tg_msg.text and "Account Information:" in tg_msg.text:
            # ডিসকর্ডের ক্যারেক্টার লিমিট এড়াতে এবং দেখতে সুন্দর লাগার জন্য কোড ব্লকে পাঠানো
            await ctx.send(f"```text\n{tg_msg.text}\n```")
            
        # যদি মিডিয়া ফাইল হয় (স্টিকার অথবা ক্যারেক্টার আউটফিট ফটো)
        elif tg_msg.media:
            # ফাইলটি সাময়িকভাবে লোকাল সার্ভারে ডাউনলোড করা
            file_path = await tg_client.download_media(tg_msg)
            if file_path:
                # ডিসকর্ডে ফাইলটি আপলোড করা
                with open(file_path, "rb") as fh:
                    discord_file = discord.File(fh)
                    await ctx.send(file=discord_file)
                
                # রেন্ডার স্টোরেজ ক্লিন রাখার জন্য ডাউনলোড করা ফাইলটি ডিলিট করা
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting temp file: {e}")

# বট রান করার মূল ড্রাইভ
if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("Error: DISCORD_TOKEN environment variable is missing! Please set it in Render dashboard.")
