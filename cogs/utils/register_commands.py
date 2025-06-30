"""
User Registration Slash Command - Function Based
==============================================

A slash command for registering users for LOL internal matches.

File: cogs/utils/register_commands.py
Author: Juan Dodam
Version: 1.1.0 - Enhanced logging
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


@app_commands.command(name='등록', description='내전 참가를 위한 유저 등록')
@app_commands.describe(
    실명='실제 이름을 입력해주세요',
    티어='현재 롤 티어를 선택해주세요',
    랭크='현재 롤 랭크를 선택해주세요',
    주포지션='주 포지션을 선택해주세요',
    부포지션='부 포지션을 선택해주세요'
)
async def register_command(
    interaction: discord.Interaction,
    실명: str,
    티어: Literal["아이언", "브론즈", "실버", "골드", "플래티넘", "에메랄드", "다이아몬드", "마스터", "그랜드마스터", "챌린저"],
    랭크: Literal["4", "3", "2", "1"],
    주포지션: Literal["탑", "정글", "미드", "원딜", "서폿"],
    부포지션: Literal["탑", "정글", "미드", "원딜", "서폿", "탑 빼고", "정글 빼고", "미드 빼고", "원딜 빼고", "서폿 빼고", "모두가능"]
):
    """
    Register a user for internal matches.
    
    Parameters:
    - 실명: User's real name
    - 티어: LOL tier
    - 랭크: LOL rank
    - 주포지션: Main position
    - 부포지션: Sub position or exclusion preference
    """
    logger = interaction.client.logger
    logger.info(f"🎯 REGISTER COMMAND STARTED by {interaction.user} ({interaction.user.id})")
    logger.debug(f"Register params: 실명={실명}, 티어={티어}, 랭크={랭크}, 주포지션={주포지션}, 부포지션={부포지션}")
    
    try:
        # Get data manager
        logger.debug("Getting data manager instance")
        dm = get_data_manager()
        
        # Validate tier and rank combination
        logger.debug(f"Validating tier {티어} and rank {랭크} combination")
        if 티어 in ["마스터", "그랜드마스터", "챌린저"] and 랭크 != "1":
            logger.warning(f"Invalid tier-rank combination: {티어} {랭크} by user {interaction.user}")
            await interaction.response.send_message(
                f"❌ {티어} 티어는 1티어만 가능합니다.", 
                ephemeral=True
            )
            return
        
        # Check if user already exists
        logger.debug(f"Checking if user {실명} already exists")
        if dm.user_exists(실명):
            logger.warning(f"User {실명} already exists, requesting clarification from {interaction.user}")
            
            # Create embed asking for clarification
            embed = discord.Embed(
                title="⚠️ 이름 중복",
                description=f"**{실명}** 이름으로 이미 등록된 유저가 있습니다.",
                color=discord.Color.orange()
            )
            
            # Get existing user data to show
            existing_user = dm.get_user(실명)
            embed.add_field(
                name="기존 등록 정보",
                value=f"티어: {existing_user['tier']} {existing_user['rank']}\n주포지션: {existing_user['main_position']}\n부포지션: {existing_user['sub_position']}",
                inline=False
            )
            
            embed.add_field(
                name="해결 방법",
                value="1️⃣ **동명이인인 경우**: 이름 옆에 숫자를 추가해주세요 (예: 김철수2)\n2️⃣ **정보 수정인 경우**: `/수정` 커맨드를 사용해주세요",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Calculate MMR
        logger.debug(f"Calculating MMR for {티어} {랭크}")
        mmr = calculate_mmr(티어, 랭크)
        logger.debug(f"Calculated MMR: {mmr}")
        
        # Add user to database
        logger.debug(f"Adding user {실명} to database with MMR {mmr}")
        success = dm.add_user(
            name=실명,
            tier=티어,
            rank=랭크,
            main_position=주포지션,
            sub_position=부포지션,
            mmr=mmr
        )
        
        if success:
            logger.info(f"✅ User {실명} registered successfully with MMR {mmr}")
            
            # Create registration confirmation embed
            embed = discord.Embed(
                title="✅ 등록 완료",
                description=f"**{실명}**님이 내전에 등록되었습니다!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="🏆 티어", 
                value=f"{티어} {랭크}", 
                inline=True
            )
            embed.add_field(
                name="⚡ MMR", 
                value=f"{mmr}", 
                inline=True
            )
            embed.add_field(
                name="🎯 주포지션", 
                value=주포지션, 
                inline=True
            )
            embed.add_field(
                name="🔄 부포지션", 
                value=부포지션, 
                inline=True
            )
            embed.add_field(
                name="📊 전적", 
                value="0승 0패 (0%)", 
                inline=True
            )
            embed.add_field(
                name="🎮 총 게임 수", 
                value="0게임", 
                inline=True
            )
            
            embed.set_footer(text=f"등록자: {interaction.user.display_name}")
            
            logger.debug("Sending registration confirmation embed")
            await interaction.response.send_message(embed=embed)
            logger.info(f"✅ Registration confirmation sent for {실명}")
            
        else:
            logger.error(f"❌ Failed to add user {실명} to database - dm.add_user returned False")
            await interaction.response.send_message(
                "❌ 등록 중 오류가 발생했습니다.", 
                ephemeral=True
            )
            
    except discord.HTTPException as e:
        logger.error(f"❌ Discord HTTP error in register command: {e}")
        logger.error(f"Error details: status={e.status}, text={e.text}")
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message(
                    "❌ 디스코드 통신 오류가 발생했습니다.", 
                    ephemeral=True
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
                
    except FileNotFoundError as e:
        logger.error(f"❌ File not found error in register command: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ 데이터 파일을 찾을 수 없습니다.", 
                ephemeral=True
            )
            
    except PermissionError as e:
        logger.error(f"❌ Permission error in register command: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ 데이터 파일 권한 오류가 발생했습니다.", 
                ephemeral=True
            )
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in register command: {type(e).__name__}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.error(f"User: {interaction.user} ({interaction.user.id})")
        logger.error(f"Guild: {interaction.guild} ({interaction.guild.id if interaction.guild else 'None'})")
        logger.error(f"Channel: {interaction.channel} ({interaction.channel.id if interaction.channel else 'None'})")
        
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message(
                    "❌ 등록 처리 중 예상치 못한 오류가 발생했습니다.", 
                    ephemeral=True
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")


@app_commands.command(name='등록확인', description='등록된 유저 정보를 확인합니다')
@app_commands.describe(
    실명='확인할 유저의 실명'
)
async def check_registration_command(
    interaction: discord.Interaction,
    실명: str
):
    """
    Check registration information for a user.
    
    Parameters:
    - 실명: User's real name to check
    """
    logger = interaction.client.logger
    logger.info(f"🎯 CHECK REGISTRATION COMMAND STARTED by {interaction.user} ({interaction.user.id})")
    logger.debug(f"Checking registration for: {실명}")
    
    try:
        # Get data manager
        logger.debug("Getting data manager instance")
        dm = get_data_manager()
        
        # Get user data
        logger.debug(f"Retrieving user data for {실명}")
        user_data = dm.get_user(실명)
        
        if not user_data:
            logger.warning(f"User not found: {실명} requested by {interaction.user}")
            await interaction.response.send_message(
                f"❌ '{실명}' 이름으로 등록된 유저를 찾을 수 없습니다.", 
                ephemeral=True
            )
            return
        
        logger.debug(f"User data retrieved: {user_data}")
        
        # Calculate win rate
        logger.debug(f"Calculating win rate for {실명}")
        winrate = dm.get_user_winrate(실명)
        winrate_text = f"{winrate:.1f}%" if winrate is not None else "0%"
        logger.debug(f"Win rate calculated: {winrate_text}")
        
        # Create user info embed
        embed = discord.Embed(
            title="👤 유저 정보",
            description=f"**{실명}**님의 등록 정보",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🏆 티어", 
            value=f"{user_data['tier']} {user_data['rank']}", 
            inline=True
        )
        embed.add_field(
            name="⚡ MMR", 
            value=f"{user_data['mmr']}", 
            inline=True
        )
        embed.add_field(
            name="🎯 주포지션", 
            value=user_data['main_position'], 
            inline=True
        )
        embed.add_field(
            name="🔄 부포지션", 
            value=user_data['sub_position'], 
            inline=True
        )
        embed.add_field(
            name="📊 전적", 
            value=f"{user_data['wins']}승 {user_data['losses']}패 ({winrate_text})", 
            inline=True
        )
        embed.add_field(
            name="🎮 총 게임 수", 
            value=f"{user_data['total_games']}게임", 
            inline=True
        )
        
        embed.set_footer(text=f"조회자: {interaction.user.display_name}")
        
        logger.debug("Sending user info embed")
        await interaction.response.send_message(embed=embed)
        logger.info(f"✅ Registration check completed for {실명}")
        
    except discord.HTTPException as e:
        logger.error(f"❌ Discord HTTP error in check registration command: {e}")
        logger.error(f"Error details: status={e.status}, text={e.text}")
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message(
                    "❌ 디스코드 통신 오류가 발생했습니다.", 
                    ephemeral=True
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")
                
    except FileNotFoundError as e:
        logger.error(f"❌ File not found error in check registration command: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ 데이터 파일을 찾을 수 없습니다.", 
                ephemeral=True
            )
            
    except Exception as e:
        logger.error(f"❌ Unexpected error in check registration command: {type(e).__name__}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        logger.error(f"User: {interaction.user} ({interaction.user.id})")
        logger.error(f"Guild: {interaction.guild} ({interaction.guild.id if interaction.guild else 'None'})")
        logger.error(f"Channel: {interaction.channel} ({interaction.channel.id if interaction.channel else 'None'})")
        logger.error(f"Requested name: {실명}")
        
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message(
                    "❌ 정보 조회 중 예상치 못한 오류가 발생했습니다.", 
                    ephemeral=True
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message: {send_error}")


# This function is required for the cog to be loaded
async def setup(bot):
    """Load the Register commands."""
    bot.tree.add_command(register_command)
    bot.tree.add_command(check_registration_command)
    bot.logger.info("Register function commands loaded successfully")