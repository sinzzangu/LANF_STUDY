"""
Ping Command Cog
================

A simple cog containing just the ping command.

File: cogs/ping.py
Author: Juan Dodam
Version: 1.0.0
"""

import time
from datetime import datetime

import discord
from discord.ext import commands


class PingCog(commands.Cog):
    """A cog containing the ping command."""
    
    def __init__(self, bot):
        """Initialize the Ping cog."""
        self.bot = bot
        self.logger = bot.logger
        
        self.logger.info("Ping cog initialized")
    
    @commands.command(name='ping')
    async def ping_command(self, ctx):
        """
        Check bot latency and response time.
        Shows both API latency and response time.
        """
        # Record start time for response calculation
        start_time = time.time()
        
        # Get bot's websocket latency
        api_latency = round(self.bot.latency * 1000)
        
        # Send initial message
        message = await ctx.send("🏓 Pinging...")
        
        # Calculate response time
        end_time = time.time()
        response_time = round((end_time - start_time) * 1000)
        
        # Create detailed embed
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        # Add latency fields
        embed.add_field(
            name="🌐 API Latency", 
            value=f"`{api_latency}ms`", 
            inline=True
        )
        embed.add_field(
            name="⚡ Response Time", 
            value=f"`{response_time}ms`", 
            inline=True
        )
        embed.add_field(
            name="🤖 Bot Status", 
            value="✅ Online", 
            inline=True
        )
        
        # Add status indicator based on latency
        if api_latency < 100:
            status_emoji = "🟢"
            status_text = "Excellent"
        elif api_latency < 200:
            status_emoji = "🟡"
            status_text = "Good"
        elif api_latency < 300:
            status_emoji = "🟠"
            status_text = "Fair"
        else:
            status_emoji = "🔴"
            status_text = "Poor"
        
        embed.add_field(
            name="📊 Connection Quality", 
            value=f"{status_emoji} {status_text}", 
            inline=True
        )
        
        # Add footer
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        
        # Edit the original message with the embed
        await message.edit(content=None, embed=embed)
        
        # Log the ping command usage
        self.logger.info(
            f"Ping command used by {ctx.author} in {ctx.guild.name if ctx.guild else 'DM'} "
            f"- API: {api_latency}ms, Response: {response_time}ms"
        )


# This function is required for the cog to be loaded
async def setup(bot):
    """Load the Ping cog."""
    await bot.add_cog(PingCog(bot))
    bot.logger.info("Ping cog loaded successfully")