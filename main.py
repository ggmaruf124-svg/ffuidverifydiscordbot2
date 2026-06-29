import asyncio
import discord
from discord.ext import commands
from telethon import TelegramClient, events

# Discord & Telethon Configuration
# (আপনার টোকেন এবং API ID/Hash এখানে বসাবেন)
bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())
tg_client = TelegramClient('session_name', API_ID, 'API_HASH')

TARGET_BOT = 'Target_Telegram_Bot_Username' # ফ্রিফায়ার বটের ইউজারনেম

@bot.command()
async def uid(ctx, uid_number: str):
    # ডিসকর্ডে ইনিশিয়াল রেসপন্স
    status_msg = await ctx.send(f"🔍 | **PROFILE FINDER** | {ctx.author.mention}, ফ্রিফায়ার UID: `{uid_number}` এর ফুল প্রোফাইল ও মিডিয়া টেলিগ্রাম থেকে আনা হচ্ছে...")
    
    # টেলিগ্রাম ক্লায়েন্ট কানেক্ট করা
    if not tg_client.is_connected():
        await tg_client.connect()

    # টেলিগ্রাম বটের মেসেজ ট্র্যাক করার জন্য ভেরিয়েবল
    received_messages = []
    loop_control = asyncio.Event()

    # টেলিগ্রাম ইভেন্ট হ্যান্ডলার: নতুন মেসেজ বা মেসেজ এডিট হলে ক্যাচ করবে
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

        # আমাদের মোট ৩টি জিনিস লাগবে (মূল টেক্সট, স্টিকার, এবং আউটফিট ইমেজ)
        # যদি ৩টি মেসেজ চলে আসে, তবে লুপ শেষ করব
        if len(received_messages) >= 3:
            loop_control.set()

    # টেলিগ্রামে কমান্ড পাঠানো
    await tg_client.send_message(TARGET_BOT, f'/get {uid_number}')

    try:
        # সর্বোচ্চ ২০ সেকেন্ড অপেক্ষা করবে সব ডাটা আসার জন্য (টাইমআউট সেফটি)
        await asyncio.wait_for(loop_control.wait(), timeout=20.0)
    except asyncio.TimeoutError:
        print("সব মেসেজ সময়মতো আসেনি, যা পাওয়া গেছে তাই পাঠানো হচ্ছে...")

    # ইভেন্ট হ্যান্ডলার রিমুভ করা যাতে পরের কমান্ডে ঝামেলা না হয়
    tg_client.remove_event_handler(handler)

    # ডিসকর্ডে ডাটা ফরওয়ার্ড করা
    if not received_messages:
        await ctx.send("❌ টেলিগ্রাম বট থেকে কোনো রেসপন্স পাওয়া যায়নি।")
        return

    # প্রথম লোডিং স্ট্যাটাস মেসেজটা ডিলিট করে দেওয়া
    try:
        await status_msg.delete()
    except:
        pass

    # সংগৃহীত মেসেজগুলো প্রসেস করা
    for tg_msg in received_messages:
        # যদি শুধু টেক্সট হয় (Account Information)
        if tg_msg.text and "Account Information:" in tg_msg.text:
            # ডিসকর্ডের ক্যারেক্টার লিমিট ২০০০, তাই সেফটির জন্য কোড ব্লকে পাঠানো
            await ctx.send(f"```text\n{tg_msg.text}\n```")
            
        # যদি মিডিয়া (স্টিকার বা image.png) হয়
        elif tg_msg.media:
            # ফাইলটি লোকালি ডাউনলোড করা
            file_path = await tg_client.download_media(tg_msg)
            if file_path:
                # ডিসকর্ডে ফাইল আপলোড করা
                with open(file_path, "rb") as fh:
                    discord_file = discord.File(fh)
                    await ctx.send(file=discord_file)
                # ডাউনলোড করা ফাইল ক্লিনআপ (ডিলিট) করা
                import os
                os.remove(file_path)

# বট রান করার কোড নিচে লিখবেন
