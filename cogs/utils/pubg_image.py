import discord
from discord import app_commands
from discord.ext import commands

# 파일 경로 미리 매핑
MAPS = {
    "에란겔": "assets/pubg_maps/1_에란겔.png",
    "미라마": "assets/pubg_maps/2_미라마.png",
    "태이고": "assets/pubg_maps/3_태이고.png",
    "데스턴": "assets/pubg_maps/4_데스턴.png",
    "비켄디": "assets/pubg_maps/5_비켄디.png",
    "카라킨": "assets/pubg_maps/6_카라킨.png",
    "파라모": "assets/pubg_maps/7_파라모.png",
}

class MapImage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="맵", description="PUBG 맵 이미지를 불러옵니다.")
    @app_commands.describe(name="맵 이름을 선택하세요")
    @app_commands.choices(name=[
        app_commands.Choice(name="에란겔", value="에란겔"),
        app_commands.Choice(name="미라마", value="미라마"),
        app_commands.Choice(name="태이고", value="태이고"),
        app_commands.Choice(name="데스턴", value="데스턴"),
        app_commands.Choice(name="비켄디", value="비켄디"),
        app_commands.Choice(name="카라킨", value="카라킨"),
        app_commands.Choice(name="파라모", value="파라모"),
    ])
    async def map_image(self, interaction: discord.Interaction, name: app_commands.Choice[str]):
        path = MAPS.get(name.value)
        if path:
            file = discord.File(path, filename=f"{name.value}.png")
            await interaction.response.send_message(file=file)
        else:
            await interaction.response.send_message("해당 맵 이미지를 찾을 수 없습니다.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MapImage(bot))