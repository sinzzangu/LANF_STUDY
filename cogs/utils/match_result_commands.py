"""
Match Result Slash Command - Function Based (Fixed Version)
==========================================================

A slash command for recording match results from team formations.
Now supports automatic detection of recent team formation results.

File: cogs/utils/match_result_commands.py
Author: Juan Dodam
Version: 2.1.0
"""

import discord
from discord import app_commands
import traceback
import re
from typing import Literal, List, Optional, Tuple
from cogs.utils.data_manager import get_data_manager


async def get_recent_team_formations(channel, limit: int = 3) -> List[Tuple[List[str], List[str], str, str]]:
    """
    채널에서 최근 팀구성 결과들을 찾습니다.
    
    Returns:
        List[Tuple[blue_team, red_team, formation_type, message_id]]
    """
    try:
        formations = []
        async for message in channel.history(limit=200):  # 더 많은 메시지 검색
            if message.author.bot and len(message.embeds) > 0:
                for embed in message.embeds:
                    # 팀구성 명령어 결과인지 확인
                    if embed.title and ("팀 구성 결과" in embed.title or "옵션" in embed.title):
                        teams = parse_team_from_embed(embed)
                        if teams:
                            blue_team, red_team = teams
                            formation_type = determine_formation_type(embed.title)
                            formations.append((blue_team, red_team, formation_type, str(message.id)))
                            
                            # 원하는 개수만큼 찾으면 중단
                            if len(formations) >= limit:
                                return formations
        return formations
    except Exception as e:
        print(f"Error getting recent team formations: {e}")
        return []


def parse_team_from_embed(embed) -> Optional[Tuple[List[str], List[str]]]:
    """
    Embed에서 블루팀/레드팀 정보를 추출합니다.
    
    Returns:
        Tuple[blue_team, red_team] or None
    """
    try:
        blue_team = []
        red_team = []
        
        for field in embed.fields:
            if "블루팀" in field.name or "🔵" in field.name:
                blue_team = extract_player_names(field.value)
            elif "레드팀" in field.name or "🔴" in field.name:
                red_team = extract_player_names(field.value)
        
        # 양쪽 팀 모두 5명씩 있어야 유효한 팀구성
        if len(blue_team) == 5 and len(red_team) == 5:
            return blue_team, red_team
        return None
    except Exception as e:
        print(f"Error parsing team from embed: {e}")
        return None


def extract_player_names(field_value: str) -> List[str]:
    """
    필드 값에서 플레이어명을 추출합니다.
    
    Examples:
        - "탑: **플레이어1** (MMR: 1200)" -> ["플레이어1"]
        - "**플레이어1** (MMR: 1200)" -> ["플레이어1"]
    """
    try:
        # **플레이어명** 패턴 매칭
        players = re.findall(r'\*\*(.*?)\*\*', field_value)
        # MMR 정보나 기타 텍스트 제거하고 순수 플레이어명만 추출
        clean_players = []
        for player in players:
            # (MMR: 숫자) 패턴 제거
            clean_name = re.sub(r'\s*\(MMR:.*?\)', '', player).strip()
            if clean_name:
                clean_players.append(clean_name)
        return clean_players
    except Exception as e:
        print(f"Error extracting player names: {e}")
        return []


def determine_formation_type(title: str) -> str:
    """
    임베드 제목에서 팀구성 방식을 결정합니다.
    """
    if "포지션+MMR" in title or ("포지션" in title and "MMR" in title):
        return "포지션 + MMR 밸런싱"
    elif "MMR만" in title or ("MMR" in title and "포지션" not in title):
        return "MMR 밸런싱만"
    elif "대안" in title or "다양성" in title:
        return "새로운 조합 추천"
    else:
        return "알 수 없는 방식"


def format_team_display(blue_team: List[str], red_team: List[str]) -> str:
    """팀 구성을 간단히 표시합니다."""
    blue_names = ", ".join(blue_team[:3]) + ("..." if len(blue_team) > 3 else "")
    red_names = ", ".join(red_team[:3]) + ("..." if len(red_team) > 3 else "")
    return f"🔵 {blue_names} vs 🔴 {red_names}"


class TeamSelectionView(discord.ui.View):
    """팀구성 선택 및 결과 입력을 위한 뷰"""
    
    def __init__(self, formations: List[Tuple[List[str], List[str], str, str]], blue_result: str):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.formations = formations
        self.blue_result = blue_result
        self.winner = "blue" if blue_result == "승" else "red"
        
        # 팀 선택 드롭다운 추가
        self.add_item(TeamSelect(formations, self))
    
    async def save_result(self, interaction: discord.Interaction, selected_index: int):
        """선택된 팀구성으로 경기 결과를 저장합니다."""
        try:
            blue_team, red_team, formation_type, message_id = self.formations[selected_index]
            
            dm = get_data_manager()
            
            # Save match (MVP 없이)
            match_id = dm.add_match(
                blue_team=blue_team,
                red_team=red_team,
                winner=self.winner,
                mvp=None  # MVP 제거
            )
            
            # Create final result embed
            winner_text = "🔵 1팀 (블루팀)" if self.winner == "blue" else "🔴 2팀 (레드팀)"
            winner_color = discord.Color.blue() if self.winner == "blue" else discord.Color.red()
            
            embed = discord.Embed(
                title="✅ 경기 결과 저장 완료",
                description=f"**{formation_type}** 방식의 경기 결과가 저장되었습니다!",
                color=winner_color
            )
            
            # Show team composition
            blue_info = [f"**{player}**" for player in blue_team]
            red_info = [f"**{player}**" for player in red_team]
            
            embed.add_field(
                name="🔵 1팀 (블루팀)",
                value="\n".join(blue_info),
                inline=True
            )
            
            embed.add_field(
                name="🔴 2팀 (레드팀)",
                value="\n".join(red_info),
                inline=True
            )
            
            embed.add_field(
                name="🏆 경기 결과",
                value=f"**승리팀**: {winner_text}\n**매치 ID**: {match_id}",
                inline=False
            )
            
            embed.set_footer(text=f"기록자: {interaction.user.display_name}")
            
            # Clear view
            self.clear_items()
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            # Log success
            logger = interaction.client.logger
            logger.info(f"✅ Match result saved: {match_id} - Winner: {self.winner}")
            
        except Exception as e:
            logger = interaction.client.logger
            logger.error(f"❌ Error saving match result: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            error_embed = discord.Embed(
                title="❌ 저장 실패",
                description="경기 결과 저장 중 오류가 발생했습니다.",
                color=discord.Color.red()
            )
            
            await interaction.response.edit_message(embed=error_embed, view=None)


class TeamSelect(discord.ui.Select):
    """팀구성 선택을 위한 드롭다운"""
    
    def __init__(self, formations: List[Tuple[List[str], List[str], str, str]], parent_view: TeamSelectionView):
        self.parent_view = parent_view
        self.formations = formations
        
        options = []
        for i, (blue_team, red_team, formation_type, message_id) in enumerate(formations):
            team_display = format_team_display(blue_team, red_team)
            options.append(
                discord.SelectOption(
                    label=f"{i+1}. {formation_type}",
                    description=team_display,
                    value=str(i),
                    emoji="⚔️"
                )
            )
        
        super().__init__(
            placeholder="경기를 진행한 팀구성을 선택해주세요...",
            options=options,
            custom_id="team_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        selected_index = int(self.values[0])
        await self.parent_view.save_result(interaction, selected_index)


@app_commands.command(name='결과', description='최근 3개의 팀구성 결과 중 선택하여 경기 결과를 기록합니다')
@app_commands.describe(
    일팀결과='1팀(블루팀)의 경기 결과를 선택해주세요'
)
@app_commands.choices(일팀결과=[
    app_commands.Choice(name="승", value="승"),
    app_commands.Choice(name="패", value="패")
])
async def match_result_command(
    interaction: discord.Interaction,
    일팀결과: app_commands.Choice[str]
):
    """
    Record match results by selecting from recent team formations in the channel.
    
    Parameters:
    - 일팀결과: Result for team 1 (blue team) - win or loss
    """
    logger = interaction.client.logger
    logger.info(f"🎯 MATCH RESULT COMMAND STARTED by {interaction.user} ({interaction.user.id})")
    
    blue_result = 일팀결과.value
    logger.debug(f"Blue team result: {blue_result}")
    
    try:
        # Defer response for longer processing time
        await interaction.response.defer()
        
        # 채널에서 최근 팀구성 결과들 찾기
        formations = await get_recent_team_formations(interaction.channel, limit=3)
        
        if not formations:
            embed = discord.Embed(
                title="❌ 팀구성 결과를 찾을 수 없습니다",
                description=(
                    "이 채널에서 최근 `/팀구성` 명령어 결과를 찾을 수 없습니다.\n\n"
                    "**해결 방법:**\n"
                    "1. 먼저 `/팀구성` 명령어를 사용해주세요\n"
                    "2. 팀구성 결과가 너무 오래되었다면 다시 팀구성을 해주세요\n"
                    "3. 다른 채널에서 팀구성을 했다면 해당 채널에서 결과를 입력해주세요"
                ),
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        logger.info(f"Found {len(formations)} team formations")
        
        # 팀 선택 뷰 표시
        winner_team_name = "🔵 1팀 (블루팀)" if blue_result == "승" else "🔴 2팀 (레드팀)"
        view = TeamSelectionView(formations, blue_result)
        
        embed = discord.Embed(
            title="⚔️ 팀구성 선택",
            description=(
                f"**승리팀**: {winner_team_name}\n\n"
                f"최근 {len(formations)}개의 팀구성 결과를 찾았습니다.\n"
                "경기를 진행한 팀구성을 선택해주세요."
            ),
            color=discord.Color.gold()
        )
        
        # 팀구성 목록 표시
        formation_list = []
        for i, (blue_team, red_team, formation_type, message_id) in enumerate(formations):
            team_display = format_team_display(blue_team, red_team)
            formation_list.append(f"`{i+1}.` **{formation_type}**\n{team_display}")
        
        embed.add_field(
            name="📋 사용 가능한 팀구성",
            value="\n\n".join(formation_list),
            inline=False
        )
        
        embed.set_footer(text="아래 드롭다운에서 해당하는 팀구성을 선택해주세요")
        
        await interaction.followup.send(embed=embed, view=view)
        
        logger.info(f"✅ Team selection interface displayed with {len(formations)} options")
        
    except discord.HTTPException as e:
        logger.error(f"❌ Discord HTTP error in match result command: {e}")
        logger.error(f"Error details: status={e.status}, text={e.text}")
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message(
                    "❌ 디스코드 통신 오류가 발생했습니다.", 
                    ephemeral=True
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
        else:
            try:
                await interaction.followup.send(
                    "❌ 디스코드 통신 오류가 발생했습니다.", 
                    ephemeral=True
                )
            except Exception as send_error:
                logger.error(f"Failed to send followup error message: {send_error}")
                
    except Exception as e:
        logger.error(f"❌ Unexpected error in match result command: {type(e).__name__}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.error(f"User: {interaction.user} ({interaction.user.id})")
        
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message(
                    "❌ 경기 결과 입력 중 예상치 못한 오류가 발생했습니다.", 
                    ephemeral=True
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
        else:
            try:
                await interaction.followup.send(
                    "❌ 경기 결과 입력 중 예상치 못한 오류가 발생했습니다.", 
                    ephemeral=True
                )
            except Exception as send_error:
                logger.error(f"Failed to send followup error message: {send_error}")


# This function is required for the cog to be loaded
async def setup(bot):
    """Load the Match Result command."""
    bot.tree.add_command(match_result_command)
    bot.logger.info("Match Result function command loaded successfully")