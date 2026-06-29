import os
import asyncio
import discord
from discord.ext import commands
from telethon import TelegramClient, events

# ================= CONFIGURATION =================
TELEGRAM_API_ID = 33809887          
TELEGRAM_API_HASH = "6d1b4c3acabca19425298ec275b0b469"
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# আপনার ফ্রিফায়ার বটের ইউজারনেম এখানে সেট করা হলো
TARGET_BOT = 'FFPlayerInfoBot' 
# =================================================

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())
tg_client = TelegramClient('session_name', TELEGRAM_API_ID, TELEGRAM_API_HASH)

@bot.event
async def on_ready():
    print(f"✅ Discord Bot is online as {bot.user}")
    if not tg_client.is_connected():
        await tg_client.start()
    print("✅ Telegram Client is connected.")

@bot.command()
async def uid(ctx, uid_number: str):
    status_msg = await ctx.send(f"🔍 | **PROFILE FINDER** | {ctx.author.mention}, ফ্রিফায়ার UID: `{uid_number}` এর ফুল প্রোফাইল ও মিডিয়া টেলিগ্রাম থেকে আনা হচ্ছে...")
    
    if not tg_client.is_connected():
        await tg_client.connect()

    # মেসেজগুলো প্রসেস করার মেইন লজিক
    async def process_tg_message(event_msg):
        msg_text = event_msg.text or ""
        
        # লোডিং মেসেজ হলে ওটা ডিসকর্ডে পাঠাবে না, ইগনোর করবে
        if "Fetching information for" in msg_text:
            return

        # মূল অ্যাকাউন্ট ইনফো থাকলে কোড ব্লকে সুন্দর করে ডিসকর্ডে পাঠাবে
        if "Account Information:" in msg_text:
            await ctx.send(f"```text\n{msg_text}\n```")
            
        # স্টিকার বা ইমেজ (মিডিয়া) থাকলে ডাউনলোড করে ডিসকর্ডে আপলোড করবে
        elif event_msg.media:
            file_path = await tg_client.download_media(event_msg)
            if file_path:
                with open(file_path, "rb") as fh:
                    await ctx.send(file=discord.File(fh))
                try:
                    os.remove(file_path) # সাময়িক ফাইল ডিলিট করা
                except:
                    pass

    # নতুন মেসেজ হ্যান্ডলার
    @tg_client.on(events.NewMessage(chats=TARGET_BOT))
    async def new_msg_handler(event):
        await process_tg_message(event.message)

    # মেসেজ এডিট হ্যান্ডলার (টেলিগ্রাম বট মেসেজ এডিট করলে যাতে ক্যাচ করতে পারে)
    @tg_client.on(events.MessageEdited(chats=TARGET_BOT))
    async def edit_msg_handler(event):
        await process_tg_message(event.message)

    # টেলিগ্রাম বটের কাছে কমান্ড পাঠানো হলো
    await tg_client.send_message(TARGET_BOT, f'/get {uid_number}')

    # ডাটা রিসিভ ও ফরওয়ার্ড করার জন্য ১৫ সেকেন্ড লাইভ অপেক্ষা করবে
    await asyncio.sleep(15)

    # কাজ শেষ হওয়ার পর হ্যান্ডলারগুলো রিমুভ করা হচ্ছে যাতে মেমোরি ফ্রি থাকে
    tg_client.remove_event_handler(new_msg_handler)
    tg_client.remove_event_handler(edit_msg_handler)

    # 'PROFILE FINDER' লোডিং মেসেজটি ডিলিট করে দেওয়া
    try:
        await status_msg.delete()
    except:
        pass

if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("Error: DISCORD_TOKEN missing in Environment Variables!")
