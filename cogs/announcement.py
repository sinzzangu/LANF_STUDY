"""
Announcement Command Cog
========================

A cog containing announcement commands for sending messages to channels.

File: cogs/announcement.py
Author: Juan Dodam
Version: 1.0.0
"""
from datetime import datetime

import discord
from discord.ext import commands


class AnnouncementCog(commands.Cog):
    """A cog containing the announcement command."""
    
    def __init__(self, bot):
        """Initialize the Announcement cog."""
        self.bot = bot
        self.logger = bot.logger
        
        self.logger.info("공지 기능 추가")
    
    @commands.command(name='공지')
    async def announcement_command(self, ctx, *, args=None):
        """
        Send announcement to a channel.
        
        Usage:
        1. !공지 <channel_name> <message> - Send to specific channel
        2. !공지 <message> - Send to current channel
        """
        # # Check if user has administrator permissions
        # if not ctx.author.guild_permissions.administrator:
        #     await ctx.send("❌ 관리자 권한이 필요합니다.")
        #     return
        
        # Check if any message was provided
        if not args:
            await ctx.send("❌ 사용법: `!공지 <채널 이름> <메시지>` 또는 `!공지 <메시지>`")
            return
        
        # Split the arguments
        parts = args.split(maxsplit=1) # 최대 2개로 나눠라, 1개는 가장 첫번째꺼, 나머지는 뒤에꺼꺼
        
        # Try to find if first part is a channel name
        potential_channel_name = parts[0]
        channel = discord.utils.get(ctx.guild.text_channels, name=potential_channel_name) # returns none if not found
        
        if channel and len(parts) == 2:
            # Case 1: !공지 channel_name message
            print("case 1")
            target_channel = channel
            message = parts[1]
            self.logger.info(f"Announcement to specific channel '{channel.name}' by {ctx.author}")
        
        elif len(parts) == 1:
            # Case 2: !공지 message (send to current channel)
            print("case 2")
            target_channel = ctx.channel
            message = parts[0]
            self.logger.info(f"Announcement to current channel '{ctx.channel.name}' by {ctx.author}")
        
        elif len(parts) == 2 and not channel:
            # Case 2: !공지 message with spaces (no channel found, treat as message)
            print("case 3")
            target_channel = ctx.channel
            message = args  # Use full args as message
            self.logger.info(f"Announcement to current channel '{ctx.channel.name}' by {ctx.author}")
        
        else:
            await ctx.send("❌ 사용법: `!공지 <채널 이름> <메시지>` 또는 `!공지 <메시지>`")
            return
        
        # Check if bot has permission to send messages in target channel
        if not target_channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(f"❌ '{target_channel.name}' 채널에 메시지를 보낼 권한이 없습니다.")
            return
        
        try:
            # Create announcement embed
            embed = discord.Embed(
                title="📢 공지사항",
                description=message,
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"공지자: {ctx.author.display_name}")
            
            # Send the announcement
            await target_channel.send(embed=embed)
            
            # Send confirmation message if announcing to different channel
            if target_channel != ctx.channel:
                await ctx.send(f"✅ '{target_channel.name}' 채널에 공지가 전송되었습니다.")
            
            # Delete the original command message
            try:
                await ctx.message.delete()
                self.logger.info(f"Deleted command message from {ctx.author}")
            except discord.NotFound:
                # Message was already deleted
                pass
            except discord.Forbidden:
                # Bot doesn't have permission to delete messages
                self.logger.warning(f"No permission to delete message in {ctx.channel.name}")
            except Exception as e:
                self.logger.error(f"Error deleting command message: {e}")
            
        except discord.Forbidden:
            await ctx.send(f"❌ '{target_channel.name}' 채널에 메시지를 보낼 권한이 없습니다.")
        except Exception as e:
            await ctx.send("❌ 공지 전송 중 오류가 발생했습니다.")
            self.logger.error(f"Error sending announcement: {e}")


# This function is required for the cog to be loaded
async def setup(bot):
    """Load the Announcement cog."""
    await bot.add_cog(AnnouncementCog(bot))
    bot.logger.info("Announcement cog loaded successfully")