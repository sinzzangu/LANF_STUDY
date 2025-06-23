import discord
from discord import app_commands
from utils import riot_api
import json
from pathlib import Path
from datetime import datetime
import logging

USERS_FILE = Path("data/registered_users.json")
MATCHES_FILE = Path("data/internal_matches.json")
MATCHES_FILE.parent.mkdir(parents=True, exist_ok=True)
if not MATCHES_FILE.exists():
    MATCHES_FILE.write_text("{}", encoding="utf-8")

def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app_commands.command(name="내전기록", description="저장된 내전 게임 기록을 확인합니다.")
async def internal_matches(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    if not MATCHES_FILE.exists():
        await interaction.followup.send("❌ 저장된 내전이 없습니다.", ephemeral=True)
        return

    matches = load_json(MATCHES_FILE)
    if not matches:
        await interaction.followup.send("📭 저장된 내전이 없습니다.", ephemeral=True)
        return

    msg_lines = [f"📋 저장된 내전 기록 (총 {len(matches)}개):\n"]
    for i, (match_id, data) in enumerate(matches.items(), 1):
        msg_lines.append(f"{i}. `{match_id}` - {', '.join(data['summoner_names'])}")
        if i >= 5:
            break

    await interaction.followup.send("\n".join(msg_lines), ephemeral=True)

@app_commands.command(name="내전저장", description="최근 내전 1개를 저장합니다.")
@app_commands.describe(riot_id="최근 게임을 한 소환사의 Riot ID (예: HideOnBush#KR1)")
async def save_internal_match(interaction: discord.Interaction, riot_id: str):
    await interaction.response.defer(ephemeral=True)

    try:
        if "#" not in riot_id:
            await interaction.followup.send("❌ Riot ID는 `이름#태그` 형식이어야 합니다.", ephemeral=True)
            return

        name, tag = riot_id.split("#")
        user_data = load_json(USERS_FILE)
        registered_puuids = {v["puuid"]: v["summoner_name"] for v in user_data.values()}

        account = await riot_api.get_account_by_riot_id(name, tag)
        recent_ids = await riot_api.get_recent_match_ids(account["puuid"], count=10)

        for match_id in recent_ids:
            match = await riot_api.get_match_detail(match_id)
            participants = match["metadata"]["participants"]
            common = [p for p in participants if p in registered_puuids]

            if len(common) == 10:
                saved = load_json(MATCHES_FILE)
                if match_id in saved:
                    await interaction.followup.send(f"⚠️ 이미 저장된 매치입니다: {match_id}", ephemeral=True)
                    return

                saved[match_id] = {
                    "match_id": match_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "puuids": common,
                    "summoner_names": [registered_puuids[p] for p in common]
                }

                save_json(MATCHES_FILE, saved)
                await interaction.followup.send(f"✅ 내전 저장 완료: `{match_id}`", ephemeral=True)
                return

        await interaction.followup.send("📭 10인 내전 매치를 찾을 수 없습니다.", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ 오류 발생: {str(e)}", ephemeral=True)

async def setup(bot):
    bot.tree.add_command(internal_matches)
    bot.tree.add_command(save_internal_match)