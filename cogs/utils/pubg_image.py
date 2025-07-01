import discord
from discord import app_commands
import os

MAPS = {
    "에란겔": "assets/pubg_maps/1.jpg",
    "미라마": "assets/pubg_maps/2.jpg",
    "태이고": "assets/pubg_maps/3.jpg",
    "데스턴": "assets/pubg_maps/4.jpg",
    "비켄디": "assets/pubg_maps/5.jpg",
    "카라킨": "assets/pubg_maps/6.jpg",
    "파라모": "assets/pubg_maps/7.jpg",
}

async def setup(bot):
    @bot.tree.command(name="맵", description="PUBG 맵 이미지를 불러옵니다.")
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
    async def map_image(interaction: discord.Interaction, name: app_commands.Choice[str]):
        # 1) 커맨드 진입 확인
        print(f"[DEBUG] /맵 호출됨: {name.value}")
        # 2) 응답 지연 알림
        await interaction.response.defer()
        try:
            path = MAPS.get(name.value)
            abs_path = os.path.abspath(path)
            print(f"[DEBUG] 절대 경로: {abs_path}")
            file = discord.File(abs_path, filename=f"{name.value}.png")
            # 3) Deferred 후에 followup으로 전송
            await interaction.followup.send(file=file)
        except Exception as e:
            # 4) 에러 발생 시 메시지 출력
            await interaction.followup.send(f"에러 발생: {e}", ephemeral=True)
            print(f"[ERROR] /맵: {e}")