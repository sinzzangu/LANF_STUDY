from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
import os
from datetime import datetime, timedelta

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# slash command
@bot.event
async def on_ready():
    if not hasattr(bot, "synced"):
        await bot.tree.sync()
        bot.synced = True
    print(f"{bot.user} All ready")

# ping command
@bot.command(name="pang")
async def ping(ctx):
    await ctx.send("Pong!")

# slash notice command
@bot.tree.command(name="공지", description="공지")
@app_commands.describe(channel="공지할 채널", message="공지 내용")
async def announce(interaction: discord.Interaction, channel: discord.TextChannel, message: str):

    embed = discord.Embed(
        title="**공지사항**",
        description=message,
        color=discord.Color.from_rgb(0, 71, 171),
        timestamp=datetime.utcnow() + timedelta(hours=9)
    )
    embed.set_footer(text=f"공지자: {interaction.user.display_name}",
                      #icon_url=interaction.user.avatar.url if interaction.user.avatar else None #아바타 표시
                      )
    
    await interaction.response.defer(ephemeral=True)
    await channel.send(embed=embed)
    await interaction.followup.send("공지 업로드 완료", ephemeral=True)

# # text notice command
# @bot.command(name="공지")
# async def announce(ctx, channel: discord.TextChannel, *, message: str):
#     embed = discord.Embed(
#         title= "공지사항",
#         description=message,
#         color=discord.Color.blue(),
#         timestamp=datetime.utcnow() + timedelta(hours=9)
#     )

#     embed.set_footer(
#         text=f"공지자: {ctx.author.display_name}",
#         icon_url=ctx.author.avatar.url if ctx.author.avatar else None #아바타 표시
#     )

#     await channel.send(embed=embed)
#     await ctx.send("공지 업로드 완료")

# #!공지 embed 공지는 탐색 불가.
# @bot.command(name="공지")
# async def latest_announcement(ctx):
#     for channel in ctx.guild.text_channels:
#         try:
#             async for message in channel.history(limit=100):
#                 if message.author == bot.user and "*공지*" in message.content:
#                     await ctx.reply(f"최근 공지({channel.mention}):\n{message.content}")
#                     return
#         except discord.Forbidden:
#             continue # 봇이 접근할 수 없는 채널 건너뛰기
#         except discord.HTTPException:
#             continue #API 요청 에러 발생 시 건너뛰기
    
#     await ctx.send("공지를 찾을 수 없습니다.")

# image
# @bot.command(name="에란겔", description="에란겔 비밀의방")
# async def fetch_images(interaction: discord.Interaction):
    
#     await interaction.response.defer()

#     image_url = [f""]

#     await interaction.followup.send("요청완료")




TOKEN = os.getenv("DISCORD_BOT_TOKEN")
print(TOKEN)


bot.run(TOKEN)