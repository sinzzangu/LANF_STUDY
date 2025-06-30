"""
Statistics Slash Command - Function Based
=========================================

A slash command for displaying user and server statistics.

File: cogs/utils/statistics_commands.py
Author: Juan Dodam
Version: 1.0.0
"""

import discord
from discord import app_commands
import traceback
from typing import Optional, Dict, List, Tuple
from collections import defaultdict
from cogs.utils.data_manager import get_data_manager


def calculate_teammate_stats(user_name: str, dm) -> Dict[str, Dict]:
    """Calculate statistics with each teammate."""
    teammate_stats = defaultdict(lambda: {"games": 0, "wins": 0})
    
    # Get all matches where user participated
    user_matches = dm.get_user_matches(user_name)
    
    for match in user_matches:
        blue_team = match.get('blue_team', [])
        red_team = match.get('red_team', [])
        winner = match.get('winner', '')
        
        # Determine if user was on blue or red team
        if user_name in blue_team:
            user_team = blue_team
            user_won = (winner == "blue")
        else:
            user_team = red_team
            user_won = (winner == "red")
        
        # Update stats for each teammate
        for teammate in user_team:
            if teammate != user_name:
                teammate_stats[teammate]["games"] += 1
                if user_won:
                    teammate_stats[teammate]["wins"] += 1
    
    # Calculate win rates
    for teammate in teammate_stats:
        games = teammate_stats[teammate]["games"]
        wins = teammate_stats[teammate]["wins"]
        teammate_stats[teammate]["winrate"] = (wins / games) * 100 if games > 0 else 0
    
    return dict(teammate_stats)


def get_best_worst_teammates(teammate_stats: Dict[str, Dict], min_games: int = 5) -> Tuple[str, str]:
    """Get best and worst teammates based on win rate (minimum games required)."""
    eligible_teammates = {
        name: stats for name, stats in teammate_stats.items() 
        if stats["games"] >= min_games
    }
    
    if not eligible_teammates:
        return None, None
    
    # Best teammate (highest win rate)
    best_teammate = max(eligible_teammates.items(), key=lambda x: x[1]["winrate"])
    
    # Worst teammate (lowest win rate)
    worst_teammate = min(eligible_teammates.items(), key=lambda x: x[1]["winrate"])
    
    return best_teammate, worst_teammate


def calculate_team_formation_reliability(dm) -> Tuple[float, int]:
    """Calculate team formation reliability and games needed for 95% confidence."""
    matches = dm.get_all_matches()
    
    if len(matches) < 10:
        return 0.0, 50 - len(matches)
    
    # Simple reliability calculation based on MMR differences
    total_games = len(matches)
    balanced_games = 0
    
    for match_data in matches.values():
        blue_team = match_data.get('blue_team', [])
        red_team = match_data.get('red_team', [])
        
        # Calculate team MMRs
        blue_mmr = sum(dm.get_user(player)['mmr'] for player in blue_team if dm.get_user(player))
        red_mmr = sum(dm.get_user(player)['mmr'] for player in red_team if dm.get_user(player))
        
        mmr_diff = abs(blue_mmr - red_mmr)
        
        # Consider game balanced if MMR difference is <= 100
        if mmr_diff <= 100:
            balanced_games += 1
    
    reliability = (balanced_games / total_games) * 100 if total_games > 0 else 0
    
    # Calculate games needed for better reliability (target: 50 games minimum)
    games_needed = max(0, 50 - total_games)
    
    return reliability, games_needed


# Create autocomplete function for player names
async def player_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    """Autocomplete function for player names."""
    try:
        dm = get_data_manager()
        all_users = dm.get_all_users()
        
        # Filter users based on current input
        filtered_users = [name for name in all_users.keys() if current.lower() in name.lower()]
        
        # Return up to 25 choices (Discord limit)
        return [
            app_commands.Choice(name=user, value=user)
            for user in filtered_users[:25]
        ]
    except:
        return []


@app_commands.command(name='통계', description='개인 또는 전체 통계를 확인합니다')
@app_commands.describe(
    유저='통계를 확인할 유저 (선택사항, 비어두면 전체 통계)'
)
@app_commands.autocomplete(유저=player_autocomplete)
async def statistics_command(
    interaction: discord.Interaction,
    유저: Optional[str] = None
):
    """
    Display individual or server-wide statistics.
    
    Parameters:
    - 유저: User to show statistics for (optional, shows server stats if empty)
    """
    logger = interaction.client.logger
    logger.info(f"🎯 STATISTICS COMMAND STARTED by {interaction.user} ({interaction.user.id})")
    logger.debug(f"Requested user: {유저}")
    
    try:
        # Get data manager
        dm = get_data_manager()
        
        if 유저:
            # Individual user statistics
            await show_individual_stats(interaction, 유저, dm, logger)
        else:
            # Server-wide statistics
            await show_server_stats(interaction, dm, logger)
            
    except discord.HTTPException as e:
        logger.error(f"❌ Discord HTTP error in statistics command: {e}")
        logger.error(f"Error details: status={e.status}, text={e.text}")
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message(
                    "❌ 디스코드 통신 오류가 발생했습니다.", 
                    ephemeral=True
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
                
    except Exception as e:
        logger.error(f"❌ Unexpected error in statistics command: {type(e).__name__}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.error(f"User: {interaction.user} ({interaction.user.id})")
        
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message(
                    "❌ 통계 조회 중 예상치 못한 오류가 발생했습니다.", 
                    ephemeral=True
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")


async def show_individual_stats(interaction: discord.Interaction, user_name: str, dm, logger):
    """Show individual user statistics."""
    logger.debug(f"Showing individual stats for {user_name}")
    
    # Check if user exists
    if not dm.user_exists(user_name):
        await interaction.response.send_message(
            f"❌ '{user_name}' 유저를 찾을 수 없습니다.", 
            ephemeral=True
        )
        return
    
    # Get user data
    user_data = dm.get_user(user_name)
    winrate = dm.get_user_winrate(user_name)
    winrate_text = f"{winrate:.1f}%" if winrate is not None else "0%"
    
    # Calculate teammate statistics
    teammate_stats = calculate_teammate_stats(user_name, dm)
    best_teammate, worst_teammate = get_best_worst_teammates(teammate_stats, min_games=5)
    
    # Create individual statistics embed
    embed = discord.Embed(
        title=f"👤 {user_name} 개인 통계",
        color=discord.Color.blue()
    )
    
    # Basic stats
    embed.add_field(
        name="🏆 전적",
        value=f"{user_data['wins']}승 {user_data['losses']}패 ({winrate_text})",
        inline=True
    )
    
    embed.add_field(
        name="⚡ MMR",
        value=f"{user_data['mmr']}",
        inline=True
    )
    
    embed.add_field(
        name="🎮 총 게임",
        value=f"{user_data['total_games']}게임",
        inline=True
    )
    
    # Position info
    embed.add_field(
        name="🎯 포지션",
        value=f"주: {user_data['main_position']}\n부: {user_data['sub_position']}",
        inline=True
    )
    
    # Teammate statistics (top 3 most played with)
    if teammate_stats:
        sorted_teammates = sorted(teammate_stats.items(), key=lambda x: x[1]["games"], reverse=True)
        top_teammates = sorted_teammates[:3]
        
        teammate_info = []
        for teammate, stats in top_teammates:
            teammate_info.append(
                f"**{teammate}**: {stats['games']}게임 ({stats['winrate']:.1f}%)"
            )
        
        embed.add_field(
            name="👥 단골 팀원",
            value="\n".join(teammate_info) if teammate_info else "데이터 없음",
            inline=True
        )
    else:
        embed.add_field(
            name="👥 단골 팀원",
            value="데이터 없음",
            inline=True
        )
    
    # Best teammate (5+ games)
    if best_teammate:
        name, stats = best_teammate
        embed.add_field(
            name="🌟 최고의 팀원",
            value=f"**{name}**\n{stats['games']}게임 ({stats['winrate']:.1f}%)",
            inline=True
        )
    
    # Worst teammate (5+ games)
    if worst_teammate:
        name, stats = worst_teammate
        embed.add_field(
            name="💀 함께해서 더러웠고..",
            value=f"**{name}**\n{stats['games']}게임 ({stats['winrate']:.1f}%)",
            inline=True
        )
    
    embed.set_footer(text=f"조회자: {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)
    logger.info(f"✅ Individual statistics displayed for {user_name}")


async def show_server_stats(interaction: discord.Interaction, dm, logger):
    """Show server-wide statistics."""
    logger.debug("Showing server-wide statistics")
    
    # Get all users and matches
    all_users = dm.get_all_users()
    total_matches = dm.get_match_count()
    
    if not all_users:
        await interaction.response.send_message(
            "❌ 등록된 유저가 없습니다.", 
            ephemeral=True
        )
        return
    
    # Calculate leaderboards
    mmr_leaderboard = dm.get_leaderboard("mmr")
    
    # Win rate leaderboard (5+ games only)
    winrate_leaderboard = []
    for user_data in mmr_leaderboard:
        if user_data["total_games"] >= 5:
            winrate = (user_data["wins"] / user_data["total_games"]) * 100
            user_data["winrate"] = winrate
            winrate_leaderboard.append(user_data)
    
    winrate_leaderboard.sort(key=lambda x: x["winrate"], reverse=True)
    
    # Most active player (most games)
    most_active = max(mmr_leaderboard, key=lambda x: x["total_games"])
    
    # Calculate team formation reliability
    reliability, games_needed = calculate_team_formation_reliability(dm)
    
    # Create server statistics embed
    embed = discord.Embed(
        title="📊 서버 전체 통계",
        color=discord.Color.green()
    )
    
    # Basic server stats
    embed.add_field(
        name="🎮 총 경기 수",
        value=f"{total_matches}경기",
        inline=True
    )
    
    embed.add_field(
        name="👥 등록된 유저",
        value=f"{len(all_users)}명",
        inline=True
    )
    
    # Average MMR
    avg_mmr = sum(user["mmr"] for user in mmr_leaderboard) / len(mmr_leaderboard)
    embed.add_field(
        name="📈 평균 MMR",
        value=f"{avg_mmr:.0f}",
        inline=True
    )
    
    # MMR ranking (top 3)
    if mmr_leaderboard:
        mmr_top3 = mmr_leaderboard[:3]
        mmr_ranking = []
        for i, user in enumerate(mmr_top3):
            mmr_ranking.append(f"{i+1}. **{user['name']}** ({user['mmr']} MMR)")
        
        embed.add_field(
            name="👑 MMR 랭킹",
            value="\n".join(mmr_ranking),
            inline=True
        )
    
    # Win rate ranking (top 3, 5+ games)
    if winrate_leaderboard:
        winrate_top3 = winrate_leaderboard[:3]
        winrate_ranking = []
        for i, user in enumerate(winrate_top3):
            winrate_ranking.append(f"{i+1}. **{user['name']}** ({user['winrate']:.1f}%)")
        
        embed.add_field(
            name="🏆 승률 랭킹",
            value="\n".join(winrate_ranking) + "\n*(5게임 이상)*",
            inline=True
        )
    
    # Most active player
    embed.add_field(
        name="🎯 내전 단골",
        value=f"**{most_active['name']}**\n{most_active['total_games']}게임 참여",
        inline=True
    )
    
    # Team formation reliability
    embed.add_field(
        name="⚖️ 팀 구성 신뢰도",
        value=f"{reliability:.1f}%\n앞으로 {games_needed}게임 더 필요",
        inline=True
    )
    
    embed.set_footer(text=f"조회자: {interaction.user.display_name}")
    
    await interaction.response.send_message(embed=embed)
    logger.info("✅ Server statistics displayed successfully")


# This function is required for the cog to be loaded
async def setup(bot):
    """Load the Statistics command."""
    bot.tree.add_command(statistics_command)
    bot.logger.info("Statistics function command loaded successfully")