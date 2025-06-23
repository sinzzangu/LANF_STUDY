import discord
from discord import app_commands
from utils import riot_api
import json
from pathlib import Path

USERS_FILE = Path("data/registered_users.json")
USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
if not USERS_FILE.exists():
    USERS_FILE.write_text("{}", encoding="utf-8")

def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app_commands.command(name="소환사등록", description="자신의 라이엇 ID를 등록합니다.")
@app_commands.describe(riot_name="라이엇 ID 이름 (예: hideonbush)띄어쓰기XXX", riot_tag="라이엇 ID 태그 (예: 1234)")
async def register(interaction: discord.Interaction, riot_name: str, riot_tag: str):
    await interaction.response.defer(ephemeral=True)

    try:
        account_data = await riot_api.get_account_by_riot_id(riot_name, riot_tag)
        puuid = account_data["puuid"]
        summoner_name = account_data.get("gameName", "")

        user_data = load_json(USERS_FILE)

        user_data[str(interaction.user.id)] = {
            "discord_name": str(interaction.user),
            "riot_name": riot_name,
            "riot_tag": riot_tag,
            "summoner_name": summoner_name,
            "puuid": puuid
        }

        save_json(USERS_FILE, user_data)

        await interaction.followup.send(
            f"✅ 등록 완료: **{riot_name}#{riot_tag}** (소환사명: {summoner_name})\nPUUID: `{puuid[:8]}...`",
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(
            f"❌ 등록 중 오류 발생: {str(e)}",
            ephemeral=True
        )

async def setup(bot):
    bot.tree.add_command(register)