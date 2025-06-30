"""
Announcement Slash Command - Function Based
==========================================

A slash command for sending announcements to channels.

File: cogs/announcement.py
Author: Juan Dodam
Version: 2.1.0 - Function based approach
"""
from datetime import datetime
from typing import Optional

import discord
from discord import app_commands


@app_commands.command(name='공지', description='채널에 공지사항을 전송합니다')
@app_commands.describe(
    message='전송할 공지 메시지',
    channel='공지를 보낼 채널 (선택사항, 기본값: 현재 채널)'
)
async def announcement_command(
    interaction: discord.Interaction, 
    message: str, 
    channel: Optional[discord.TextChannel] = None
):
    """
    Send announcement to a channel.
    
    Parameters:
    - message: The announcement message to send
    - channel: Optional channel to send to (defaults to current channel)
    """
    # 시작 로그
    print(f"🎯 ANNOUNCEMENT COMMAND STARTED by {interaction.user}")
    
    # Check if user has administrator permissions
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 관리자 권한이 필요합니다.", ephemeral=True)
        return
    
    # Determine target channel
    target_channel = channel if channel else interaction.channel
    
    # Check if bot has permission to send messages in target channel
    if not target_channel.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message(
            f"❌ '{target_channel.name}' 채널에 메시지를 보낼 권한이 없습니다.", 
            ephemeral=True
        )
        return
    
    try:
        # Send immediate response to prevent timeout
        if target_channel != interaction.channel:
            confirmation_msg = f"✅ '{target_channel.name}' 채널에 공지를 전송합니다..."
        else:
            confirmation_msg = "✅ 공지를 전송합니다..."
        
        await interaction.response.send_message(confirmation_msg, ephemeral=True)
        print(f"🎯 Initial response sent")
        
        # Create announcement embed
        embed = discord.Embed(
            title="📢 공지사항",
            description=message,
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"공지자: {interaction.user.display_name}")
        
        # Send the announcement
        await target_channel.send(embed=embed)
        
        # Update the response
        if target_channel != interaction.channel:
            final_msg = f"✅ '{target_channel.name}' 채널에 공지가 전송되었습니다."
        else:
            final_msg = "✅ 공지가 전송되었습니다."
        
        await interaction.edit_original_response(content=final_msg)
        print(f"🎯 ANNOUNCEMENT COMMAND COMPLETED successfully")
        
    except discord.Forbidden:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"❌ '{target_channel.name}' 채널에 메시지를 보낼 권한이 없습니다.", 
                ephemeral=True
            )
        else:
            await interaction.edit_original_response(
                content=f"❌ '{target_channel.name}' 채널에 메시지를 보낼 권한이 없습니다."
            )
    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ 공지 전송 중 오류가 발생했습니다.", 
                ephemeral=True
            )
        else:
            await interaction.edit_original_response(
                content="❌ 공지 전송 중 오류가 발생했습니다."
            )
        print(f"🎯 Error in announcement: {e}")


# This function is required for the cog to be loaded
async def setup(bot):
    """Load the Announcement command."""
    bot.tree.add_command(announcement_command)
    bot.logger.info("Announcement function command loaded successfully")