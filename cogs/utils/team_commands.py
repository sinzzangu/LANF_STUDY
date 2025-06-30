"""
Team Formation Slash Command - Enhanced with Multiple Balancing Options
======================================================================

A slash command for creating balanced teams for LOL internal matches with 3 different balancing strategies.

File: cogs/utils/team_commands.py
Author: Juan Dodam
Version: 2.0.1
"""

import discord
from discord import app_commands
import traceback
import random
from datetime import datetime  # 추가된 import
from typing import List, Dict, Any, Tuple, Optional
from cogs.utils.data_manager import get_data_manager


def calculate_adjusted_mmr(player: str, dm) -> int:
    """Calculate MMR adjusted by win rate from match history with confidence scaling."""
    user_data = dm.get_user(player)
    if not user_data:
        return 1000  # Default MMR
    
    base_mmr = user_data['mmr']
    
    # Get match history
    matches = dm.get_user_matches(player)
    if not matches:
        return base_mmr
    
    # Calculate overall win rate
    total_games = len(matches)
    wins = sum(1 for match in matches if match.get('result') == 'win')
    win_rate = wins / total_games if total_games > 0 else 0.5
    
    # Confidence scaling based on total number of games
    if total_games < 5:
        confidence = 0.1  # 5경기 미만: 거의 반영 안함
    elif total_games < 10:
        confidence = 0.2  # 5-9경기: 20% 반영
    elif total_games < 15:
        confidence = 0.4  # 10-14경기: 40% 반영
    elif total_games < 25:
        confidence = 0.6  # 15-24경기: 60% 반영
    elif total_games < 35:
        confidence = 0.8  # 25-34경기: 80% 반영
    else:
        confidence = 1.0  # 35경기 이상: 100% 반영
    
    # Adjust MMR based on win rate with confidence scaling
    max_adjustment = 200 * confidence  # 신뢰도에 따라 최대 조정값 스케일링
    win_rate_adjustment = (win_rate - 0.5) * 2 * max_adjustment
    adjusted_mmr = base_mmr + win_rate_adjustment
    
    return int(adjusted_mmr)


def calculate_recent_form_mmr(player: str, dm) -> int:
    """Calculate MMR based on recent 5 games performance with confidence scaling."""
    user_data = dm.get_user(player)
    if not user_data:
        return 1000
    
    base_mmr = user_data['mmr']
    
    # Get match history
    matches = dm.get_user_matches(player)
    if not matches:
        return base_mmr
    
    # Get recent matches (group by date, take only 5 most recent match dates)
    matches_by_date = {}
    for match in matches:
        match_date = match.get('date', datetime.now().strftime('%Y-%m-%d'))
        if match_date not in matches_by_date:
            matches_by_date[match_date] = []
        matches_by_date[match_date].append(match)
    
    # Sort dates and take 5 most recent
    recent_dates = sorted(matches_by_date.keys(), reverse=True)[:5]
    recent_matches = []
    for date in recent_dates:
        # Take one representative match per date (latest one)
        recent_matches.append(matches_by_date[date][-1])
    
    if not recent_matches:
        return base_mmr
    
    # Calculate recent win rate
    recent_wins = sum(1 for match in recent_matches if match.get('result') == 'win')
    recent_win_rate = recent_wins / len(recent_matches)
    recent_games_count = len(recent_matches)
    
    # Confidence scaling based on number of recent games
    if recent_games_count == 1:
        confidence = 0.2  # 1경기: 20% 신뢰도
    elif recent_games_count == 2:
        confidence = 0.4  # 2경기: 40% 신뢰도  
    elif recent_games_count == 3:
        confidence = 0.6  # 3경기: 60% 신뢰도
    elif recent_games_count == 4:
        confidence = 0.8  # 4경기: 80% 신뢰도
    else:  # 5+ games
        confidence = 1.0  # 5경기 이상: 100% 신뢰도
    
    # Apply confidence-scaled adjustment
    max_adjustment = 300 * confidence  # 신뢰도에 따라 최대 조정값 스케일링
    form_adjustment = (recent_win_rate - 0.5) * 2 * max_adjustment
    adjusted_mmr = base_mmr + form_adjustment
    
    return int(adjusted_mmr)


def calculate_team_mmr_adjusted(players: List[str], dm, mmr_type: str = "base") -> int:
    """Calculate total MMR for a team with different MMR calculation methods."""
    total_mmr = 0
    for player in players:
        if mmr_type == "adjusted":
            mmr = calculate_adjusted_mmr(player, dm)
        elif mmr_type == "recent":
            mmr = calculate_recent_form_mmr(player, dm)
        else:  # base
            user_data = dm.get_user(player)
            mmr = user_data['mmr'] if user_data else 1000
        total_mmr += mmr
    return total_mmr


def get_player_positions(players: List[str], dm) -> Dict[str, List[str]]:
    """Get position preferences for players."""
    position_map = {
        "탑": [],
        "정글": [],
        "미드": [],
        "원딜": [],
        "서폿": []
    }
    
    flexible_players = []
    
    for player in players:
        user_data = dm.get_user(player)
        if user_data:
            main_pos = user_data['main_position']
            sub_pos = user_data['sub_position']
            
            # 주포지션은 항상 추가
            position_map[main_pos].append(player)
            
            # 주포지션 = 부포지션인 경우: 해당 포지션만 가능 (다른 포지션 배치 불가)
            if main_pos == sub_pos:
                continue  # 주포지션만 추가하고 다른 포지션은 추가하지 않음
            
            # 부포지션 처리
            if sub_pos == "모두가능":
                flexible_players.append(player)
            elif sub_pos.endswith(" 빼고"):
                excluded = sub_pos.replace(" 빼고", "")
                for pos in position_map.keys():
                    if pos != excluded and pos != main_pos:
                        if player not in position_map[pos]:
                            position_map[pos].append(player)
            elif sub_pos in position_map and sub_pos != main_pos:
                position_map[sub_pos].append(player)
    
    # 모든 포지션 가능한 플레이어들을 각 포지션에 추가
    for player in flexible_players:
        for pos in position_map.keys():
            if player not in position_map[pos]:
                position_map[pos].append(player)
    
    return position_map


def get_position_availability_info(players: List[str], dm) -> str:
    """Get detailed information about position availability for debugging."""
    position_map = get_player_positions(players, dm)
    info_lines = []
    
    for pos, candidates in position_map.items():
        info_lines.append(f"{pos}: {len(candidates)}명 ({', '.join(candidates)})")
    
    return "\n".join(info_lines)


def balance_teams_option1(players: List[str], dm) -> Tuple[Optional[List[str]], Optional[List[str]], Optional[str]]:
    """Option 1: Win rate adjusted MMR + Position consideration."""
    if len(players) != 10:
        return None, None, "정확히 10명의 플레이어가 필요합니다."
    
    position_map = get_player_positions(players, dm)
    
    # Check if all positions can be filled and provide detailed error message
    insufficient_positions = []
    for pos, candidates in position_map.items():
        if len(candidates) < 2:
            insufficient_positions.append(f"{pos}({len(candidates)}명)")
    
    if insufficient_positions:
        position_info = get_position_availability_info(players, dm)
        error_msg = (f"포지션별 플레이어가 부족합니다: {', '.join(insufficient_positions)}\n\n"
                    f"현재 포지션별 가능 인원:\n{position_info}")
        return None, None, error_msg
    
    best_blue = None
    best_red = None
    best_mmr_diff = float('inf')
    
    for _ in range(1500):  # More iterations for better balance
        blue_team = []
        red_team = []
        used_players = set()
        success = True
        
        for position in ["탑", "정글", "미드", "원딜", "서폿"]:
            available = [p for p in position_map[position] if p not in used_players]
            if len(available) < 2:
                success = False
                break
            
            selected = random.sample(available, 2)
            blue_team.append(selected[0])
            red_team.append(selected[1])
            used_players.update(selected)
        
        if not success:
            continue
        
        blue_mmr = calculate_team_mmr_adjusted(blue_team, dm, "adjusted")
        red_mmr = calculate_team_mmr_adjusted(red_team, dm, "adjusted")
        mmr_diff = abs(blue_mmr - red_mmr)
        
        if mmr_diff < best_mmr_diff:
            best_mmr_diff = mmr_diff
            best_blue = blue_team.copy()
            best_red = red_team.copy()
    
    return best_blue, best_red, None if best_blue else "팀 밸런싱에 실패했습니다."


def balance_teams_option2(players: List[str], dm) -> Tuple[Optional[List[str]], Optional[List[str]], Optional[str]]:
    """Option 2: Win rate adjusted MMR only (ignore positions)."""
    if len(players) != 10:
        return None, None, "정확히 10명의 플레이어가 필요합니다."
    
    # Calculate adjusted MMR for all players
    player_mmrs = [(player, calculate_adjusted_mmr(player, dm)) for player in players]
    player_mmrs.sort(key=lambda x: x[1], reverse=True)  # Sort by MMR descending
    
    best_blue = None
    best_red = None
    best_mmr_diff = float('inf')
    
    # Try different combinations focusing on MMR balance
    for _ in range(2000):
        shuffled_players = [p[0] for p in player_mmrs]
        random.shuffle(shuffled_players)
        
        blue_team = shuffled_players[:5]
        red_team = shuffled_players[5:]
        
        blue_mmr = calculate_team_mmr_adjusted(blue_team, dm, "adjusted")
        red_mmr = calculate_team_mmr_adjusted(red_team, dm, "adjusted")
        mmr_diff = abs(blue_mmr - red_mmr)
        
        if mmr_diff < best_mmr_diff:
            best_mmr_diff = mmr_diff
            best_blue = blue_team.copy()
            best_red = red_team.copy()
    
    return best_blue, best_red, None


def balance_teams_option3(players: List[str], dm, option1_teams: Tuple, option2_teams: Tuple) -> Tuple[Optional[List[str]], Optional[List[str]], Optional[str]]:
    """Option 3: Alternative team composition for variety (different from options 1&2)."""
    if len(players) != 10:
        return None, None, "정확히 10명의 플레이어가 필요합니다."
    
    # Get teams from previous options to avoid
    avoid_teams = set()
    if option1_teams[0] and option1_teams[1]:
        avoid_teams.add(tuple(sorted(option1_teams[0])))
        avoid_teams.add(tuple(sorted(option1_teams[1])))
    if option2_teams[0] and option2_teams[1]:
        avoid_teams.add(tuple(sorted(option2_teams[0])))
        avoid_teams.add(tuple(sorted(option2_teams[1])))
    
    best_blue = None
    best_red = None
    best_mmr_diff = float('inf')
    
    # Use base adjusted MMR (not recent form) for consistency
    for _ in range(2000):
        shuffled_players = players.copy()
        random.shuffle(shuffled_players)
        
        blue_team = shuffled_players[:5]
        red_team = shuffled_players[5:]
        
        # Skip if this team composition matches previous options
        if (tuple(sorted(blue_team)) in avoid_teams or 
            tuple(sorted(red_team)) in avoid_teams):
            continue
        
        # Use same MMR calculation as option 2 for fair comparison
        blue_mmr = calculate_team_mmr_adjusted(blue_team, dm, "adjusted")
        red_mmr = calculate_team_mmr_adjusted(red_team, dm, "adjusted")
        mmr_diff = abs(blue_mmr - red_mmr)
        
        if mmr_diff < best_mmr_diff:
            best_mmr_diff = mmr_diff
            best_blue = blue_team.copy()
            best_red = red_team.copy()
    
    return best_blue, best_red, None if best_blue else "새로운 팀 구성을 찾지 못했습니다."


def create_team_embed(option_num: int, option_name: str, blue_team: List[str], red_team: List[str], 
                     dm, mmr_type: str = "base", color: discord.Color = discord.Color.blue(), 
                     show_positions: bool = True) -> discord.Embed:
    """Create embed for team composition."""
    embed = discord.Embed(
        title=f"⚔️ 옵션 {option_num}: {option_name}",
        color=color
    )
    
    positions = ["탑", "정글", "미드", "원딜", "서폿"]
    
    # Blue team info
    blue_info = []
    for i, player in enumerate(blue_team):
        user_data = dm.get_user(player)
        if mmr_type == "adjusted":
            mmr = calculate_adjusted_mmr(player, dm)
        elif mmr_type == "recent":
            mmr = calculate_recent_form_mmr(player, dm)
        else:
            mmr = user_data['mmr'] if user_data else 1000
        
        if show_positions and len(blue_team) == 5 and i < 5:  # Position-based team
            blue_info.append(f"{positions[i]}: **{player}** (MMR: {mmr})")
        else:  # MMR-only team
            blue_info.append(f"**{player}** (MMR: {mmr})")
    
    embed.add_field(
        name="🔵 블루팀",
        value="\n".join(blue_info),
        inline=True
    )
    
    # Red team info
    red_info = []
    for i, player in enumerate(red_team):
        user_data = dm.get_user(player)
        if mmr_type == "adjusted":
            mmr = calculate_adjusted_mmr(player, dm)
        elif mmr_type == "recent":
            mmr = calculate_recent_form_mmr(player, dm)
        else:
            mmr = user_data['mmr'] if user_data else 1000
        
        if show_positions and len(red_team) == 5 and i < 5:  # Position-based team
            red_info.append(f"{positions[i]}: **{player}** (MMR: {mmr})")
        else:  # MMR-only team
            red_info.append(f"**{player}** (MMR: {mmr})")
    
    embed.add_field(
        name="🔴 레드팀",
        value="\n".join(red_info),
        inline=True
    )
    
    # Team statistics
    blue_mmr = calculate_team_mmr_adjusted(blue_team, dm, mmr_type)
    red_mmr = calculate_team_mmr_adjusted(red_team, dm, mmr_type)
    mmr_diff = abs(blue_mmr - red_mmr)
    
    embed.add_field(
        name="📊 팀 통계",
        value=f"🔵 블루팀 MMR: {blue_mmr}\n🔴 레드팀 MMR: {red_mmr}\n⚖️ MMR 차이: {mmr_diff}",
        inline=False
    )
    
    # Balance indicator
    if mmr_diff <= 30:
        balance_emoji = "🟢"
        balance_text = "매우 균형잡힘"
    elif mmr_diff <= 60:
        balance_emoji = "🟡"
        balance_text = "균형잡힘"
    elif mmr_diff <= 100:
        balance_emoji = "🟠"
        balance_text = "약간 불균형"
    else:
        balance_emoji = "🔴"
        balance_text = "불균형"
    
    embed.add_field(
        name="⚖️ 밸런스 상태",
        value=f"{balance_emoji} {balance_text}",
        inline=True
    )
    
    return embed


# Create autocomplete function for player names
async def player_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Autocomplete function for player names."""
    try:
        dm = get_data_manager()
        all_users = dm.get_all_users()
        
        filtered_users = [name for name in all_users.keys() if current.lower() in name.lower()]
        
        return [
            app_commands.Choice(name=user, value=user)
            for user in filtered_users[:25]
        ]
    except:
        return []


@app_commands.command(name='팀구성', description='10명의 플레이어로 3가지 밸런싱 옵션의 팀을 구성합니다')
@app_commands.describe(
    플레이어1='첫 번째 플레이어',
    플레이어2='두 번째 플레이어',
    플레이어3='세 번째 플레이어',
    플레이어4='네 번째 플레이어',
    플레이어5='다섯 번째 플레이어',
    플레이어6='여섯 번째 플레이어',
    플레이어7='일곱 번째 플레이어',
    플레이어8='여덟 번째 플레이어',
    플레이어9='아홉 번째 플레이어',
    플레이어10='열 번째 플레이어'
)
@app_commands.autocomplete(플레이어1=player_autocomplete)
@app_commands.autocomplete(플레이어2=player_autocomplete)
@app_commands.autocomplete(플레이어3=player_autocomplete)
@app_commands.autocomplete(플레이어4=player_autocomplete)
@app_commands.autocomplete(플레이어5=player_autocomplete)
@app_commands.autocomplete(플레이어6=player_autocomplete)
@app_commands.autocomplete(플레이어7=player_autocomplete)
@app_commands.autocomplete(플레이어8=player_autocomplete)
@app_commands.autocomplete(플레이어9=player_autocomplete)
@app_commands.autocomplete(플레이어10=player_autocomplete)
async def team_formation_command(
    interaction: discord.Interaction,
    플레이어1: str,
    플레이어2: str,
    플레이어3: str,
    플레이어4: str,
    플레이어5: str,
    플레이어6: str,
    플레이어7: str,
    플레이어8: str,
    플레이어9: str,
    플레이어10: str
):
    """
    Create balanced teams from 10 selected players with 3 different balancing options.
    
    Parameters:
    - 플레이어1~10: Names of 10 players to form teams
    """
    logger = interaction.client.logger
    logger.info(f"🎯 ENHANCED TEAM FORMATION COMMAND STARTED by {interaction.user} ({interaction.user.id})")
    
    players = [플레이어1, 플레이어2, 플레이어3, 플레이어4, 플레이어5, 
              플레이어6, 플레이어7, 플레이어8, 플레이어9, 플레이어10]
    
    logger.debug(f"Selected players: {players}")
    
    try:
        # Get data manager
        dm = get_data_manager()
        
        # Validate all players exist and remove duplicates
        unique_players = []
        seen = set()
        invalid_players = []
        
        for player in players:
            if player in seen:
                continue
            
            if not dm.user_exists(player):
                invalid_players.append(player)
            else:
                unique_players.append(player)
                seen.add(player)
        
        # Check for invalid players
        if invalid_players:
            logger.warning(f"Invalid players selected: {invalid_players}")
            await interaction.response.send_message(
                f"❌ 다음 플레이어들을 찾을 수 없습니다: {', '.join(invalid_players)}", 
                ephemeral=True
            )
            return
        
        # Check if exactly 10 unique players
        if len(unique_players) != 10:
            logger.warning(f"Invalid player count: {len(unique_players)} (need 10)")
            await interaction.response.send_message(
                f"❌ 정확히 10명의 서로 다른 플레이어를 선택해야 합니다. (현재: {len(unique_players)}명)", 
                ephemeral=True
            )
            return
        
        # Defer response for longer processing time
        await interaction.response.defer()
        
        logger.debug("Starting team balancing with 3 options")
        
        # Generate 3 different team compositions
        option1_teams = balance_teams_option1(unique_players, dm)
        option2_teams = balance_teams_option2(unique_players, dm)
        option3_teams = balance_teams_option3(unique_players, dm, option1_teams, option2_teams)
        
        embeds = []
        
        # Create embeds for each successful option
        if option1_teams[0] and option1_teams[1]:
            embed1 = create_team_embed(
                1, "승률기반 포지션+MMR 고려", 
                option1_teams[0], option1_teams[1], 
                dm, "adjusted", discord.Color.blue(), 
                show_positions=True
            )
            embeds.append(embed1)
        elif option1_teams[2]:  # Error message
            error_embed = discord.Embed(
                title="❌ 옵션 1: 승률기반 포지션+MMR 고려 실패",
                description=option1_teams[2],
                color=discord.Color.red()
            )
            embeds.append(error_embed)
        
        if option2_teams[0] and option2_teams[1]:
            embed2 = create_team_embed(
                2, "승률기반 MMR만 고려", 
                option2_teams[0], option2_teams[1], 
                dm, "adjusted", discord.Color.green(),
                show_positions=False
            )
            embeds.append(embed2)
        
        if option3_teams[0] and option3_teams[1]:
            embed3 = create_team_embed(
                3, "다양성을 위한 대안 구성", 
                option3_teams[0], option3_teams[1], 
                dm, "adjusted", discord.Color.purple(),
                show_positions=False
            )
            embeds.append(embed3)
        
        if not embeds:
            await interaction.followup.send("❌ 모든 팀 구성 옵션에서 균형잡힌 팀을 만들 수 없습니다.", ephemeral=True)
            return
        
        # Create main embed with explanation
        main_embed = discord.Embed(
            title="🎯 다중 옵션 팀 구성 결과",
            description=(
                "**3가지 밸런싱 방식으로 팀을 구성했습니다:**\n\n"
                "🔵 **옵션 1**: 승률을 반영한 MMR + 포지션 고려\n"
                "🟢 **옵션 2**: 승률을 반영한 MMR만 고려 (포지션 무시)\n"
                "🟣 **옵션 3**: 다양성을 위한 대안 구성 (위 옵션들과 다른 조합)\n\n"
                "각 옵션은 승률 50% 근접을 목표로 합니다."
            ),
            color=discord.Color.gold()
        )
        main_embed.set_footer(text=f"팀 구성자: {interaction.user.display_name}")
        
        # Send main embed first, then individual option embeds
        await interaction.followup.send(embed=main_embed)
        
        for embed in embeds:
            await interaction.followup.send(embed=embed)
        
        logger.info(f"✅ Enhanced team formation completed with {len(embeds)} options")
        
    except discord.HTTPException as e:
        logger.error(f"❌ Discord HTTP error in enhanced team formation command: {e}")
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
        logger.error(f"❌ Unexpected error in enhanced team formation command: {type(e).__name__}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.error(f"User: {interaction.user} ({interaction.user.id})")
        logger.error(f"Selected players: {players}")
        
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message(
                    "❌ 팀 구성 중 예상치 못한 오류가 발생했습니다.", 
                    ephemeral=True
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
        else:
            try:
                await interaction.followup.send(
                    "❌ 팀 구성 중 예상치 못한 오류가 발생했습니다.", 
                    ephemeral=True
                )
            except Exception as send_error:
                logger.error(f"Failed to send followup error message: {send_error}")


# This function is required for the cog to be loaded
async def setup(bot):
    """Load the Enhanced Team Formation command."""
    bot.tree.add_command(team_formation_command)
    bot.logger.info("Enhanced Team Formation function command loaded successfully")