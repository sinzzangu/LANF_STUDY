"""
롤 내전 봇 - 등록 및 팀 밸런싱 시스템
=====================================

실명, 티어 등록 및 전적 관리로 5:5 팀 밸런싱을 제공하는 시스템

File: cogs/utils/register.py
"""

import discord
from discord import app_commands
import json
import itertools
from typing import List, Dict, Tuple
import math

DATA_FILE = "players.json"

# 티어별 점수 (MMR 계산용)
TIER_SCORES = {
    "IRON": {"IV": 400, "III": 450, "II": 500, "I": 550},
    "BRONZE": {"IV": 600, "III": 650, "II": 700, "I": 750},
    "SILVER": {"IV": 800, "III": 850, "II": 900, "I": 950},
    "GOLD": {"IV": 1000, "III": 1050, "II": 1100, "I": 1150},
    "PLATINUM": {"IV": 1200, "III": 1250, "II": 1300, "I": 1350},
    "EMERALD": {"IV": 1400, "III": 1450, "II": 1500, "I": 1550},
    "DIAMOND": {"IV": 1600, "III": 1650, "II": 1700, "I": 1750},
    "MASTER": {"I": 1800},
    "GRANDMASTER": {"I": 1900},
    "CHALLENGER": {"I": 2000}
}


def load_data():
    """플레이어 데이터를 불러옵니다."""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_data(data):
    """플레이어 데이터를 저장합니다."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def calculate_mmr(tier: str, rank: str, wins: int, losses: int) -> int:
    """티어, 랭크, 승패를 바탕으로 MMR을 계산합니다."""
    base_mmr = TIER_SCORES.get(tier.upper(), {}).get(rank.upper(), 1000)
    
    total_games = wins + losses
    if total_games == 0:
        return base_mmr
    
    win_rate = wins / total_games
    
    # 승률에 따른 보정 (50% 기준으로 ±100 MMR)
    win_rate_adjustment = (win_rate - 0.5) * 200
    
    # 게임 수에 따른 신뢰도 보정 (많이 할수록 보정값 감소)
    confidence = min(1.0, total_games / 50)
    
    adjusted_mmr = base_mmr + (win_rate_adjustment * confidence)
    return int(adjusted_mmr)


def find_balanced_teams(players: List[str], player_data: Dict, num_options: int = 3) -> List[Tuple[List[str], List[str], float, int]]:
    """10명의 플레이어로 균형잡힌 5:5 팀을 여러 옵션으로 생성합니다."""
    if len(players) != 10:
        raise ValueError("정확히 10명의 플레이어가 필요합니다.")
    
    # 각 플레이어의 MMR 계산
    player_mmrs = {}
    for player in players:
        if player in player_data:
            data = player_data[player]
            mmr = calculate_mmr(
                data.get("tier", "GOLD"), 
                data.get("rank", "IV"),
                data.get("wins", 0),
                data.get("losses", 0)
            )
            player_mmrs[player] = mmr
        else:
            player_mmrs[player] = 1000  # 기본 MMR
    
    team_options = []
    
    # 모든 5명 조합을 확인하고 상위 옵션들 저장
    for team1 in itertools.combinations(players, 5):
        team2 = [p for p in players if p not in team1]
        
        team1_mmr = sum(player_mmrs[p] for p in team1)
        team2_mmr = sum(player_mmrs[p] for p in team2)
        
        difference = abs(team1_mmr - team2_mmr)
        
        # 예상 승률 계산
        team1_avg = team1_mmr / 5
        team2_avg = team2_mmr / 5
        mmr_diff = team1_avg - team2_avg
        win_probability = 1 / (1 + math.exp(-mmr_diff / 400))
        
        team_options.append((list(team1), team2, win_probability, difference))
    
    # MMR 차이 기준으로 정렬 (가장 균형잡힌 순)
    team_options.sort(key=lambda x: x[3])
    
    # 상위 옵션들 중에서 다양성을 고려하여 선택
    selected_options = []
    selected_options.append(team_options[0])  # 가장 균형잡힌 팀
    
    # 나머지 옵션들은 겹치는 멤버 수를 고려하여 선택
    for option in team_options[1:]:
        if len(selected_options) >= num_options:
            break
            
        # 기존 선택된 옵션들과 겹치는 멤버 수 계산
        is_diverse = True
        for selected in selected_options:
            overlap = len(set(option[0]) & set(selected[0]))
            if overlap >= 4:  # 4명 이상 겹치면 너무 비슷함
                is_diverse = False
                break
        
        if is_diverse:
            selected_options.append(option)
    
    return selected_options[:num_options]


@app_commands.command(name="등록", description="실명과 티어를 등록합니다")
@app_commands.describe(
    real_name="본인의 실명", 
    tier="티어 (IRON, BRONZE, SILVER, GOLD, PLATINUM, EMERALD, DIAMOND, MASTER, GRANDMASTER, CHALLENGER)",
    rank="랭크 (I, II, III, IV) - MASTER 이상은 I만 가능"
)
@app_commands.choices(tier=[
    app_commands.Choice(name="아이언", value="IRON"),
    app_commands.Choice(name="브론즈", value="BRONZE"),
    app_commands.Choice(name="실버", value="SILVER"),
    app_commands.Choice(name="골드", value="GOLD"),
    app_commands.Choice(name="플래티넘", value="PLATINUM"),
    app_commands.Choice(name="에메랄드", value="EMERALD"),
    app_commands.Choice(name="다이아몬드", value="DIAMOND"),
    app_commands.Choice(name="마스터", value="MASTER"),
    app_commands.Choice(name="그랜드마스터", value="GRANDMASTER"),
    app_commands.Choice(name="챌린저", value="CHALLENGER")
])
@app_commands.choices(rank=[
    app_commands.Choice(name="I", value="I"),
    app_commands.Choice(name="II", value="II"),
    app_commands.Choice(name="III", value="III"),
    app_commands.Choice(name="IV", value="IV")
])
async def register_command(interaction: discord.Interaction, real_name: str, tier: str, rank: str):
    """등록 명령어 - 실명과 티어를 등록"""
    print(f"📝 REGISTER COMMAND STARTED by {interaction.user} - {real_name}, {tier} {rank}")
    
    # 마스터 이상은 I만 허용
    if tier in ["MASTER", "GRANDMASTER", "CHALLENGER"] and rank != "I":
        await interaction.response.send_message("❌ 마스터 이상 티어는 I만 가능합니다.", ephemeral=True)
        return
    
    # 티어 검증
    if tier not in TIER_SCORES or rank not in TIER_SCORES[tier]:
        await interaction.response.send_message("❌ 올바르지 않은 티어 또는 랭크입니다.", ephemeral=True)
        return
    
    data = load_data()
    
    # 기존 데이터가 있으면 전적 유지, 없으면 새로 생성
    if real_name in data:
        data[real_name]["tier"] = tier
        data[real_name]["rank"] = rank
        status = "수정"
    else:
        data[real_name] = {
            "tier": tier,
            "rank": rank,
            "wins": 0,
            "losses": 0,
            "discord_id": interaction.user.id
        }
        status = "등록"
    
    save_data(data)
    
    mmr = calculate_mmr(tier, rank, data[real_name]["wins"], data[real_name]["losses"])
    
    await interaction.response.send_message(
        f"✅ {status} 완료: **{real_name}** - {tier} {rank} (MMR: {mmr})\n"
        f"전적: {data[real_name]['wins']}승 {data[real_name]['losses']}패"
    )
    print(f"✅ REGISTER COMMAND COMPLETED: {real_name} - {tier} {rank}")


@app_commands.command(name="전적", description="내전 전적을 기록합니다")
@app_commands.describe(
    winner_names="승리팀 멤버들 (쉼표로 구분)",
    loser_names="패배팀 멤버들 (쉼표로 구분)"
)
async def record_match(interaction: discord.Interaction, winner_names: str, loser_names: str):
    """전적 기록 명령어"""
    print(f"🏆 RECORD MATCH STARTED by {interaction.user}")
    
    data = load_data()
    
    winners = [name.strip() for name in winner_names.split(",")]
    losers = [name.strip() for name in loser_names.split(",")]
    
    if len(winners) != 5 or len(losers) != 5:
        await interaction.response.send_message("❌ 각 팀은 정확히 5명이어야 합니다.", ephemeral=True)
        return
    
    # 등록되지 않은 플레이어 확인
    unregistered = []
    for player in winners + losers:
        if player not in data:
            unregistered.append(player)
    
    if unregistered:
        await interaction.response.send_message(
            f"❌ 등록되지 않은 플레이어: {', '.join(unregistered)}", 
            ephemeral=True
        )
        return
    
    # 전적 업데이트
    for winner in winners:
        data[winner]["wins"] += 1
    
    for loser in losers:
        data[loser]["losses"] += 1
    
    save_data(data)
    
    await interaction.response.send_message(
        f"✅ 전적 기록 완료!\n"
        f"🏆 승리팀: {', '.join(winners)}\n"
        f"😢 패배팀: {', '.join(losers)}"
    )
    print(f"✅ MATCH RECORDED: Winners: {winners}, Losers: {losers}")


@app_commands.command(name="팀짜기", description="등록된 10명으로 균형잡힌 5:5 팀을 여러 옵션으로 만듭니다")
@app_commands.describe(
    player_names="참가자 10명의 실명 (쉼표로 구분)",
    options="팀 조합 옵션 수 (1-5, 기본값: 3)"
)
@app_commands.choices(options=[
    app_commands.Choice(name="1개 (가장 균형잡힌 팀만)", value=1),
    app_commands.Choice(name="2개", value=2),
    app_commands.Choice(name="3개 (기본)", value=3),
    app_commands.Choice(name="4개", value=4),
    app_commands.Choice(name="5개", value=5)
])
async def create_teams(interaction: discord.Interaction, player_names: str, options: int = 3):
    """팀 생성 명령어"""
    print(f"⚖️ CREATE TEAMS STARTED by {interaction.user}")
    
    data = load_data()
    players = [name.strip() for name in player_names.split(",")]
    
    if len(players) != 10:
        await interaction.response.send_message("❌ 정확히 10명의 플레이어가 필요합니다.", ephemeral=True)
        return
    
    # 등록되지 않은 플레이어 확인
    unregistered = [p for p in players if p not in data]
    if unregistered:
        await interaction.response.send_message(
            f"❌ 등록되지 않은 플레이어: {', '.join(unregistered)}", 
            ephemeral=True
        )
        return
    
    try:
        team_options = find_balanced_teams(players, data, options)
        
        # 팀 정보 생성 함수
        def get_team_info(team):
            team_info = []
            total_mmr = 0
            for player in team:
                player_data = data[player]
                mmr = calculate_mmr(
                    player_data["tier"], 
                    player_data["rank"],
                    player_data["wins"],
                    player_data["losses"]
                )
                total_mmr += mmr
                win_rate = (player_data["wins"] / max(player_data["wins"] + player_data["losses"], 1)) * 100
                team_info.append(f"**{player}** ({player_data['tier']} {player_data['rank']}, MMR: {mmr}, 승률: {win_rate:.1f}%)")
            
            return team_info, total_mmr
        
        # 메인 임베드
        main_embed = discord.Embed(
            title=f"⚖️ 팀 조합 옵션 ({len(team_options)}개)",
            color=0x00ff00,
            description="아래 옵션 중 하나를 선택하세요! 🎯"
        )
        
        embeds = [main_embed]
        
        # 각 옵션별로 임베드 생성
        for i, (team1, team2, win_prob, mmr_diff) in enumerate(team_options, 1):
            team1_info, team1_mmr = get_team_info(team1)
            team2_info, team2_mmr = get_team_info(team2)
            
            balance_percentage = win_prob * 100
            
            # 밸런스 점수 계산 (50%에 가까울수록 높은 점수)
            balance_score = 100 - abs(balance_percentage - 50) * 2
            
            # 밸런스 등급 결정
            if balance_score >= 95:
                balance_grade = "🏆 완벽"
                color = 0x00ff00
            elif balance_score >= 90:
                balance_grade = "⭐ 우수"
                color = 0x99ff00
            elif balance_score >= 80:
                balance_grade = "👍 양호"
                color = 0xffff00
            else:
                balance_grade = "⚠️ 보통"
                color = 0xff9900
            
            option_embed = discord.Embed(
                title=f"🎲 옵션 {i} - {balance_grade} (밸런스: {balance_score:.1f}점)",
                color=color,
                description=f"**예상 승률**: Team A {balance_percentage:.1f}% vs Team B {100-balance_percentage:.1f}%"
            )
            
            option_embed.add_field(
                name="🔵 Team A",
                value="\n".join(team1_info) + f"\n**팀 총 MMR: {team1_mmr}**",
                inline=False
            )
            
            option_embed.add_field(
                name="🔴 Team B", 
                value="\n".join(team2_info) + f"\n**팀 총 MMR: {team2_mmr}**",
                inline=False
            )
            
            option_embed.add_field(
                name="📊 상세 분석",
                value=f"MMR 차이: {mmr_diff}\n"
                      f"Team A 평균 MMR: {team1_mmr//5}\n"
                      f"Team B 평균 MMR: {team2_mmr//5}",
                inline=False
            )
            
            # 옵션 특징 설명
            if i == 1:
                option_embed.set_footer(text="💡 가장 균형잡힌 조합입니다")
            else:
                overlap_players = set(team1) & set(team_options[0][0])
                if len(overlap_players) <= 2:
                    option_embed.set_footer(text="🔄 멤버 구성이 많이 달라 새로운 조합을 경험할 수 있습니다")
                else:
                    option_embed.set_footer(text="🎯 균형과 다양성을 고려한 대안 조합입니다")
            
            embeds.append(option_embed)
        
        # 모든 임베드 전송
        await interaction.response.send_message(embeds=embeds)
        print(f"✅ TEAMS CREATED: {len(team_options)} options provided")
        
    except Exception as e:
        await interaction.response.send_message(f"❌ 팀 생성 중 오류 발생: {str(e)}", ephemeral=True)
        print(f"❌ TEAM CREATION ERROR: {e}")


@app_commands.command(name="선수명단", description="등록된 모든 선수 목록을 확인합니다")
async def player_list(interaction: discord.Interaction):
    """선수 명단 조회 명령어"""
    data = load_data()
    
    if not data:
        await interaction.response.send_message("❌ 등록된 선수가 없습니다.", ephemeral=True)
        return
    
    # MMR 순으로 정렬
    sorted_players = []
    for name, info in data.items():
        mmr = calculate_mmr(info["tier"], info["rank"], info["wins"], info["losses"])
        total_games = info["wins"] + info["losses"]
        win_rate = (info["wins"] / max(total_games, 1)) * 100
        sorted_players.append((name, info, mmr, win_rate, total_games))
    
    sorted_players.sort(key=lambda x: x[2], reverse=True)  # MMR 내림차순
    
    embed = discord.Embed(title="📋 등록된 선수 명단", color=0x0099ff)
    
    player_list_text = []
    for i, (name, info, mmr, win_rate, total_games) in enumerate(sorted_players, 1):
        player_list_text.append(
            f"{i}. **{name}** - {info['tier']} {info['rank']}\n"
            f"   MMR: {mmr} | 전적: {info['wins']}승 {info['losses']}패 ({win_rate:.1f}%)"
        )
    
    # 50명씩 나누어 여러 필드로 표시
    for i in range(0, len(player_list_text), 10):
        chunk = player_list_text[i:i+10]
        embed.add_field(
            name=f"선수 목록 ({i+1}-{min(i+10, len(player_list_text))})",
            value="\n\n".join(chunk),
            inline=False
        )
    
    embed.set_footer(text=f"총 {len(sorted_players)}명 등록됨")
    
    await interaction.response.send_message(embed=embed)


@app_commands.command(name="내정보", description="본인의 등록 정보를 확인합니다")
@app_commands.describe(real_name="확인할 실명 (없으면 본인 정보)")
async def my_info(interaction: discord.Interaction, real_name: str = None):
    """개인 정보 조회 명령어"""
    data = load_data()
    
    if real_name:
        target_name = real_name
    else:
        # Discord ID로 찾기
        target_name = None
        for name, info in data.items():
            if info.get("discord_id") == interaction.user.id:
                target_name = name
                break
        
        if not target_name:
            await interaction.response.send_message("❌ 등록된 정보를 찾을 수 없습니다. 먼저 /등록 명령어를 사용해주세요.", ephemeral=True)
            return
    
    if target_name not in data:
        await interaction.response.send_message(f"❌ '{target_name}' 선수의 정보를 찾을 수 없습니다.", ephemeral=True)
        return
    
    info = data[target_name]
    mmr = calculate_mmr(info["tier"], info["rank"], info["wins"], info["losses"])
    total_games = info["wins"] + info["losses"]
    win_rate = (info["wins"] / max(total_games, 1)) * 100
    
    embed = discord.Embed(
        title=f"👤 {target_name} 선수 정보",
        color=0x00ff00
    )
    
    embed.add_field(name="🏆 티어", value=f"{info['tier']} {info['rank']}", inline=True)
    embed.add_field(name="📊 MMR", value=str(mmr), inline=True)
    embed.add_field(name="🎮 총 게임", value=f"{total_games}게임", inline=True)
    embed.add_field(name="✅ 승리", value=f"{info['wins']}승", inline=True)
    embed.add_field(name="❌ 패배", value=f"{info['losses']}패", inline=True)
    embed.add_field(name="📈 승률", value=f"{win_rate:.1f}%", inline=True)
    
    await interaction.response.send_message(embed=embed)


# 필수: Cog 로딩 함수
async def setup(bot):
    bot.tree.add_command(register_command)
    bot.tree.add_command(record_match)
    bot.tree.add_command(create_teams)
    bot.tree.add_command(player_list)
    bot.tree.add_command(my_info)
    bot.logger.info("롤 내전 봇 시스템이 성공적으로 로드되었습니다.")