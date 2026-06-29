import os
import asyncio
import discord
from discord.ext import commands
from telethon import TelegramClient, events

# ================= CONFIGURATION =================
TELEGRAM_API_ID = 33809887          
TELEGRAM_API_HASH = "6d1b4c3acabca19425298ec275b0b469"

# রেন্ডারের Environment Variables থেকে মানগুলো নেওয়া হচ্ছে
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")  

TARGET_BOT = 'FFPlayerInfoBot' 
# =================================================

bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())
tg_client = TelegramClient('bot_session', TELEGRAM_API_ID, TELEGRAM_API_HASH)

@bot.event
async def on_ready():
    print(f"✅ Discord Bot is online as {bot.user}")
    
    # টোকেন সঠিকভাবে রেন্ডার থেকে লোড হয়েছে কিনা তা নিশ্চিত করা
    if not TG_BOT_TOKEN:
        print("❌ ERROR: 'TG_BOT_TOKEN' environment variable is missing or empty!")
        return

    # টেলিগ্রাম ক্লায়েন্ট কানেক্ট করা
    if not tg_client.is_connected():
        await tg_client.connect()
    
    # ওটিপি বা ফোন নাম্বার ইনপুট এড়াতে সরাসরি bot.sign_in পদ্ধতি ব্যবহার করা হলো
    if not await tg_client.is_user_authorized():
        try:
            await tg_client.sign_in(bot_token=TG_BOT_TOKEN)
            print("✅ Telegram Bot Client is authorized and connected seamlessly!")
        except Exception as e:
            print(f"❌ Telegram login failed: {e}")
    else:
        print("✅ Telegram Bot Client is already authorized.")

@bot.command()
async def uid(ctx, uid_number: str):
    status_msg = await ctx.send(f"🔍 | **PROFILE FINDER** | {ctx.author.mention}, ফ্রিফায়ার UID: `{uid_number}` এর ফুল প্রোফাইল ও মিডিয়া টেলিগ্রাম থেকে আনা হচ্ছে...")
    
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

    # টেলিগ্রাম বটের কাছে কমান্ড পাঠানো হলো
    await tg_client.send_message(TARGET_BOT, f'/get {uid_number}')

    # ডাটা রিসিভ করার জন্য ১৫ সেকেন্ড অপেক্ষা করবে
    await asyncio.sleep(15)

    tg_client.remove_event_handler(new_msg_handler)
    tg_client.remove_event_handler(edit_msg_handler)

    try:
        await status_msg.delete()
    except:
        pass

if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("Error: DISCORD_TOKEN missing in Environment Variables!")
