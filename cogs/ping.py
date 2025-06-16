"""
Ping Slash Command - Function Based
===================================

A slash command for checking bot latency and response time.

File: cogs/ping.py
Author: Juan Dodam
Version: 2.1.0 - Function based approach
"""

import time
from datetime import datetime

import discord
from discord import app_commands


@app_commands.command(name='ping', description='Check bot latency and response time')
async def ping_command(interaction: discord.Interaction):
    """
    Check bot latency and response time.
    Shows both API latency and response time.
    """
    # 시작 로그
    print(f"🎯 PING COMMAND STARTED by {interaction.user}")
    
    # Record start time for response calculation
    start_time = time.time()
    
    # Get bot's websocket latency
    api_latency = round(interaction.client.latency * 1000)
    
    # Send immediate response (MUST be within 3 seconds)
    await interaction.response.send_message("🏓 Pinging...", ephemeral=True)
    print(f"🎯 Initial response sent")
    
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
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    
    # Edit the original response with the embed
    try:
        await interaction.edit_original_response(content=None, embed=embed)
        print(f"🎯 PING COMMAND COMPLETED successfully")
        
    except Exception as e:
        print(f"🎯 Error updating ping response: {e}")


# This function is required for the cog to be loaded
async def setup(bot):
    """Load the Ping command."""
    bot.tree.add_command(ping_command)
    bot.logger.info("Ping function command loaded successfully")