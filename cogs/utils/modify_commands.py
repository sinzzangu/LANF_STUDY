"""
User Modification Slash Command - Function Based
==============================================

A slash command for modifying existing user registration information.

File: cogs/utils/modify_commands.py
Author: Juan Dodam
Version: 1.0.0
"""

import discord
from discord import app_commands
from typing import Literal
import traceback
from cogs.utils.data_manager import get_data_manager


# MMR calculation based on tier and rank
MMR_TABLE = {
    "아이언": {"4": 400, "3": 450, "2": 500, "1": 550},
    "브론즈": {"4": 600, "3": 650, "2": 700, "1": 750},
    "실버": {"4": 800, "3": 850, "2": 900, "1": 950},
    "골드": {"4": 1000, "3": 1050, "2": 1100, "1": 1150},
    "플래티넘": {"4": 1200, "3": 1250, "2": 1300, "1": 1350},
    "에메랄드": {"4": 1400, "3": 1450, "2": 1500, "1": 1550},
    "다이아몬드": {"4": 1600, "3": 1650, "2": 1700, "1": 1750},
    "마스터": {"1": 1800},
    "그랜드마스터": {"1": 1900},
    "챌린저": {"1": 2000}
}


def calculate_mmr(tier: str, rank: str) -> int:
    """Calculate MMR based on tier and rank."""
    if tier in MMR_TABLE:
        if rank in MMR_TABLE[tier]:
            return MMR_TABLE[tier][rank]
    
    # Default to Iron 4 if tier/rank not found
    return 400


@app_commands.command(name='수정', description='등록된 유저 정보를 수정합니다')
@app_commands.describe(
    실명='수정할 유저의 실명',
    티어='새로운 롤 티어를 선택해주세요 (선택사항)',
    랭크='새로운 롤 랭크를 선택해주세요 (선택사항)',
    주포지션='새로운 주 포지션을 선택해주세요 (선택사항)',
    부포지션='새로운 부 포지션을 선택해주세요 (선택사항)'
)
async def modify_command(
    interaction: discord.Interaction,
    실명: str,
    티어: Literal["아이언", "브론즈", "실버", "골드", "플래티넘", "에메랄드", "다이아몬드", "마스터", "그랜드마스터", "챌린저"] = None,
    랭크: Literal["4", "3", "2", "1"] = None,
    주포지션: Literal["탑", "정글", "미드", "원딜", "서폿"] = None,
    부포지션: Literal["탑", "정글", "미드", "원딜", "서폿", "탑 빼고", "정글 빼고", "미드 빼고", "원딜 빼고", "서폿 빼고", "모두가능"] = None
):
    """
    Modify existing user registration information.
    
    Parameters:
    - 실명: User's real name to modify
    - 티어: New LOL tier (optional)
    - 랭크: New LOL rank (optional)
    - 주포지션: New main position (optional)
    - 부포지션: New sub position (optional)
    """
    logger = interaction.client.logger
    logger.info(f"🎯 MODIFY COMMAND STARTED by {interaction.user} ({interaction.user.id})")
    logger.debug(f"Modify params: 실명={실명}, 티어={티어}, 랭크={랭크}, 주포지션={주포지션}, 부포지션={부포지션}")
    
    try:
        # Get data manager
        logger.debug("Getting data manager instance")
        dm = get_data_manager()
        
        # Check if user exists
        logger.debug(f"Checking if user {실명} exists")
        if not dm.user_exists(실명):
            logger.warning(f"User not found for modification: {실명} by {interaction.user}")
            await interaction.response.send_message(
                f"❌ '{실명}' 이름으로 등록된 유저를 찾을 수 없습니다.", 
                ephemeral=True
            )
            return
        
        # Get existing user data
        existing_user = dm.get_user(실명)
        logger.debug(f"Existing user data: {existing_user}")
        
        # Check if any parameters were provided
        if not any([티어, 랭크, 주포지션, 부포지션]):
            logger.warning(f"No modification parameters provided by {interaction.user}")
            await interaction.response.send_message(
                "❌ 수정할 정보를 하나 이상 입력해주세요.", 
                ephemeral=True
            )
            return
        
        # Validate tier and rank combination if both are provided
        final_tier = 티어 if 티어 else existing_user['tier']
        final_rank = 랭크 if 랭크 else existing_user['rank']
        
        logger.debug(f"Validating final tier {final_tier} and rank {final_rank} combination")
        if final_tier in ["마스터", "그랜드마스터", "챌린저"] and final_rank != "1":
            logger.warning(f"Invalid tier-rank combination in modification: {final_tier} {final_rank} by user {interaction.user}")
            await interaction.response.send_message(
                f"❌ {final_tier} 티어는 1티어만 가능합니다.", 
                ephemeral=True
            )
            return
        
        # Prepare update data
        update_data = {}
        changes = []
        
        if 티어:
            update_data['tier'] = 티어
            changes.append(f"티어: {existing_user['tier']} → {티어}")
        
        if 랭크:
            update_data['rank'] = 랭크
            changes.append(f"랭크: {existing_user['rank']} → {랭크}")
        
        if 주포지션:
            update_data['main_position'] = 주포지션
            changes.append(f"주포지션: {existing_user['main_position']} → {주포지션}")
        
        if 부포지션:
            update_data['sub_position'] = 부포지션
            changes.append(f"부포지션: {existing_user['sub_position']} → {부포지션}")
        
        # Recalculate MMR if tier or rank changed
        if 티어 or 랭크:
            new_mmr = calculate_mmr(final_tier, final_rank)
            update_data['mmr'] = new_mmr
            changes.append(f"MMR: {existing_user['mmr']} → {new_mmr}")
            logger.debug(f"Recalculated MMR: {new_mmr}")
        
        # Update user data
        logger.debug(f"Updating user {실명} with data: {update_data}")
        success = dm.update_user(실명, **update_data)
        
        if success:
            logger.info(f"✅ User {실명} modified successfully")
            
            # Create modification confirmation embed
            embed = discord.Embed(
                title="✅ 정보 수정 완료",
                description=f"**{실명}**님의 정보가 수정되었습니다!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="🔄 변경사항",
                value="\n".join(changes),
                inline=False
            )
            
            # Show updated info
            updated_user = dm.get_user(실명)
            embed.add_field(
                name="📋 수정된 정보",
                value=f"티어: {updated_user['tier']} {updated_user['rank']}\nMMR: {updated_user['mmr']}\n주포지션: {updated_user['main_position']}\n부포지션: {updated_user['sub_position']}",
                inline=False
            )
            
            embed.set_footer(text=f"수정자: {interaction.user.display_name}")
            
            logger.debug("Sending modification confirmation embed")
            await interaction.response.send_message(embed=embed)
            logger.info(f"✅ Modification confirmation sent for {실명}")
            
        else:
            logger.error(f"❌ Failed to update user {실명} - dm.update_user returned False")
            await interaction.response.send_message(
                "❌ 정보 수정 중 오류가 발생했습니다.", 
                ephemeral=True
            )
            
    except discord.HTTPException as e:
        logger.error(f"❌ Discord HTTP error in modify command: {e}")
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
        logger.error(f"❌ Unexpected error in modify command: {type(e).__name__}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.error(f"User: {interaction.user} ({interaction.user.id})")
        
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message(
                    "❌ 정보 수정 중 예상치 못한 오류가 발생했습니다.", 
                    ephemeral=True
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")


# This function is required for the cog to be loaded
async def setup(bot):
    """Load the Modify command."""
    bot.tree.add_command(modify_command)
    bot.logger.info("Modify function command loaded successfully")