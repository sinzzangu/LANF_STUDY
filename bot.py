#!/usr/bin/env python3
"""
Discord Bot Class
=================
Clean bot class definition without implementation details.
All utility functions are handled by utils/utils.py

Author: Juan Dodam
Version: 3.0.0 - Modular Structure
"""

import discord
from discord import app_commands
from utils.utils import (
    initialize_bot,
    setup_bot,
    on_bot_ready,
    handle_command_error,
    log_interaction,
    handle_guild_join,
    handle_bot_shutdown
)


class SlashBot(discord.Client):
    """Discord bot that uses slash commands exclusively."""
    
    def __init__(self):
        """Initialize bot using settings from settings.py."""
        initialize_bot(self)
    
    async def setup_hook(self):
        """Load all cogs and sync commands on startup."""
        await setup_bot(self)
    
    async def on_ready(self):
        """Bot ready event."""
        await on_bot_ready(self)
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle slash command errors."""
        await handle_command_error(self, interaction, error)
    
    async def on_interaction(self, interaction: discord.Interaction):
        """Log all interactions."""
        await log_interaction(self, interaction)
        await super().on_interaction(interaction)
    
    async def on_guild_join(self, guild):
        """Sync commands when joining a new guild."""
        await handle_guild_join(self, guild)
    
    async def close(self):
        """Handle bot shutdown."""
        await handle_bot_shutdown(self)
        await super().close()