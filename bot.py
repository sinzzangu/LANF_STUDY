from dotenv import load_dotenv
import discord
from discord.ext import commands
import os

env_path = r"C:\Users\jslee\OneDrive\바탕 화면\dibot\.env"

# .env 로드
loaded = load_dotenv(dotenv_path=env_path)

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ping command
@bot.command(name="pang")
async def pang(ctx):
    await ctx.send("Pong!")

# 
@bot.command(name="ch")
async def send_to_channel(ctx, channel_name: str, *, message: str):
    # 현재 서버(길드)의 텍스트 채널 중 이름이 일치하는 채널 찾기
    target_channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)

    if target_channel is None:
        await ctx.send(f"❌ 존재하지 않는 채널입니다")
    else:
        await target_channel.send(message)
        await ctx.send(f"✅")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print("✅ Commands loaded:", [cmd.name for cmd in bot.commands])

# 메인 실행
if __name__ == "__main__":
    bot.run(TOKEN)






#print(TOKEN)


#bot.run(TOKEN)

#print(intents)
#bot.run(token)