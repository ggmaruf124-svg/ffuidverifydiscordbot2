import discord
from discord.ext import commands
import asyncio
import re
from telethon import TelegramClient, events

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==================== [ আপনার সেটিংস ] ====================
VERIFICATION_CHANNEL_ID = 1519973711925477406  # ডিসকর্ড ভেরিফিকেশন চ্যানেল আইডি
GUILD_MEMBER_ROLE_ID = 1518691461544153289   # গিল্ড মেম্বার রোল আইডি
YOUR_GUILD_ID = "3068049967"    # আপনার ফ্রিফায়ার ইন-গেম গিল্ডের ID

DISCORD_BOT_TOKEN = "MTUxODkxNDkwMzI5NjA0OTIyMg.GHoPnI.TUpKMLSHQvepnvm9XxV6LeEwBIwEW9W-BU4g54"

# টেলিগ্রাম ক্লায়েন্ট সেটিংস (আপনার API ID এবং HASH দিন)
TELEGRAM_API_ID = 33809887          # আপনার টেলিগ্রাম API ID (Integer)
TELEGRAM_API_HASH = "6d1b4c3acabca19425298ec275b0b469"

# আপনার সচল টেলিগ্রাম বটের ইউজারনেম
TARGET_TELEGRAM_BOT = "@FFPlayerInfoBot" 
# ==========================================================

tg_client = TelegramClient('discord_tg_bridge', TELEGRAM_API_ID, TELEGRAM_API_HASH)

@bot.event
async def on_ready():
    print(f'---------------------------------------------')
    print(f'Discord Bot {bot.user.name} হিসেবে রেডি!')
    print("টেলিগ্রাম ক্লায়েন্ট কানেক্ট করা হচ্ছে...")
    await tg_client.start()
    print("টেলিগ্রাম ক্লায়েন্ট সফলভাবে ব্যাকএন্ডে রানিং!")
    print(f'---------------------------------------------')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == VERIFICATION_CHANNEL_ID:
        uid = message.content.strip()

        if not uid.isdigit():
            await message.reply("❌ দয়া করে শুধুমাত্র আপনার ফ্রিফায়ার UID টাইপ করুন।")
            return

        status_message = await message.reply("🎮 | GUILD VERIFICATION |🔄 আপনার UID ডাটাবেজে সার্চ করা হচ্ছে... অনুগ্রহ করে ধৈর্য ধরুন।")
        
        bot_peer = TARGET_TELEGRAM_BOT.replace("@", "")

        loop = asyncio.get_running_loop()
        reply_future = loop.create_future()

        # ১. নতুন মেসেজের লিসেনার
        @tg_client.on(events.NewMessage(from_users=bot_peer))
        async def handle_new_message(event):
            text = event.message.text
            if "fetching" not in text.lower() and ("guild" in text.lower() or "uid" in text.lower()):
                if not reply_future.done():
                    reply_future.set_result(text)
                    tg_client.remove_event_handler(handle_new_message)

        # ২. এডিটেড মেসেজের লিসেনার
        @tg_client.on(events.MessageEdited(from_users=bot_peer))
        async def handle_edited_message(event):
            text = event.message.text
            if "fetching" not in text.lower() and ("guild" in text.lower() or "uid" in text.lower()):
                if not reply_future.done():
                    reply_future.set_result(text)
                    tg_client.remove_event_handler(handle_edited_message)

        try:
            print(f"DEBUG: Sending /get {uid} to {TARGET_TELEGRAM_BOT}")
            await tg_client.send_message(TARGET_TELEGRAM_BOT, f"/get {uid}")
            
            # ফুল ইনফো আসার জন্য সর্বোচ্চ ৯০ সেকেন্ড অপেক্ষা করবে
            reply_text = await asyncio.wait_for(reply_future, timeout=90.0)
            
            print(f"DEBUG: Successfully Received Full Info Text.")
            
            # --- [ নতুন ও বুলেটপ্রুফ গিল্ড আইডি স্ক্র্যাপিং লজিক ] ---
            player_guild = None
            
            # মেসেজটিকে লাইনে লাইনে ভাগ করে চেক করবে
            for line in reply_text.split('\n'):
                line_lower = line.lower()
                # যে লাইনে 'guild' এবং 'id' দুটোই আছে, সেটা ধরবে (লিডারের আইডির লাইন এড়াতে 'leader' থাকা যাবে না)
                if "guild" in line_lower and "id" in line_lower and "leader" not in line_lower:
                    # ওই লাইন থেকে সব লেখা ও চিহ্ন মুছে শুধু নম্বর বের করবে
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        player_guild = numbers[0]
                        break

            # ব্যাকআপ চেক: যদি কোনো কারণে উপরের লুপ মিস করে, তবে র-টেক্সট সার্চ
            if not player_guild and YOUR_GUILD_ID in reply_text:
                player_guild = YOUR_GUILD_ID

            print(f"DEBUG: Extracted Guild ID -> '{player_guild}' (Expected: '{YOUR_GUILD_ID}')")
            
            # --- [ ডিসকর্ড রোল দেওয়ার ফাইনাল লজিক ] ---
            if player_guild:
                if str(player_guild).strip() == str(YOUR_GUILD_ID).strip():
                    discord_guild = message.guild
                    member = discord_guild.get_member(message.author.id)
                    role = discord_guild.get_role(GUILD_MEMBER_ROLE_ID)
                    
                    if role and member:
                        await member.add_roles(role)
                        await status_message.edit(content=f"✅ অভিনন্দন {message.author.mention}! আপনার আইডি আমাদের গিল্ডে পাওয়া গেছে। আপনাকে সফলভাবে মেম্বার রোল দেওয়া হয়েছে। 🎉")
                    else:
                        await status_message.edit(content="❌ ডিসকর্ড রোল পারমিশন সমস্যার কারণে রোল দেওয়া যায়নি। সার্ভার সেটিংসে বটের রোলটি সবার উপরে দিন।")
                else:
                    await status_message.edit(content=f"❌ দুঃখিত {message.author.mention}, আপনি আমাদের ইন-গেম গিল্ডে নেই। ভেরিফিকেশনের আগে গিল্ডে জয়েন করুন।")
            else:
                await status_message.edit(content="❌ দুঃখিত! আমাদের ডাটাবেজে আপনার ইউআইডি (UID) পাওয়া যায়নি।")
                
        except asyncio.TimeoutError:
            print("DEBUG ERROR: Telegram Bot did not reply in time.")
            await status_message.edit(content="⚠️ ফুল ইনফো আসতে দেরি হচ্ছে। অনুগ্রহ করে একটু পর আবার চেষ্টা করুন।")
        finally:
            try: tg_client.remove_event_handler(handle_new_message)
            except: pass
            try: tg_client.remove_event_handler(handle_edited_message)
            except: pass

    await bot.process_commands(message)

async def main():
    async with tg_client:
        await bot.start(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())