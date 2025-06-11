#!/usr/bin/env python3
"""
Discord Bot
=====================================
minimal main.py that only handles bot initialization and connection.
All functionality is handled by cogs loaded from the cogs directory.
All configuration is handled by settings.py.

Author: Juan Dodam
Version: 1.0.1
"""

import asyncio
from pathlib import Path

import discord
from discord.ext import commands

# Import bot settings
import settings

class MinimalBot(commands.Bot):
    """Minimal Discord bot that loads all functionality from cogs."""
    
    def __init__(self):
        """Initialize bot using settings from settings.py."""
        # Set up logger first
        self.logger = settings.get_configured_logger()
        
        # Log startup info
        settings.log_bot_startup(self.logger)
        
        super().__init__(
            command_prefix=settings.COMMAND_PREFIX,
            intents=settings.get_intents(),
            help_command=None,
            case_insensitive=True,
            description=settings.BOT_DESCRIPTION
        )
    
    async def setup_hook(self):
        """Load all cogs on startup."""
        if settings.AUTO_LOAD_COGS:
            await self.load_all_cogs()
    
    async def load_all_cogs(self):
        """Load all cog files from the cogs directory."""
        cogs_dir = Path("cogs")
        
        if not cogs_dir.exists():
            self.logger.warning(f"Cogs directory not found: {cogs_dir}")
            return
        
        loaded = 0
        for cog_file in cogs_dir.glob("*.py"):
            if cog_file.name.startswith("_"):
                continue
            # print(cog_file)
            cog_name = f"cogs.{cog_file.stem}" # strip .py
            # print(file_path.stem)    # Output: "ping"
            # print(file_path.suffix)  # Output: ".py"
            # print(file_path.name)    # Output: "ping.py"
            
            try:
                await self.load_extension(cog_name)
                """
                1. Imports the module (import cogs.ping)
                2. Finds the setup() function in that module
                3. Calls setup(bot) automatically
                4. Registers all commands/events from the cog
                5. Tracks the extension so it can be unloaded later
                """
                self.logger.info(f"✅ Loaded cog: {cog_name}")
                loaded += 1
            except Exception as e:
                self.logger.error(f"❌ Failed to load cog {cog_name}: {e}")
        
        self.logger.info(f"📦 Loaded {loaded} cogs total")
    
    async def on_ready(self):
        """Bot ready event."""
        self.logger.info(f"🚀 {self.user} is online!")
        self.logger.info(f"📊 Connected to {len(self.guilds)} guilds")
        self.logger.info(f"🔧 Prefix: {settings.COMMAND_PREFIX}")
        
        # Set simple bot presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"for commands | {settings.COMMAND_PREFIX}help"
        )
        await self.change_presence(activity=activity)
    
    async def close(self):
        """Handle bot shutdown."""
        settings.log_bot_shutdown(self.logger)
        await super().close()

async def main():
    """Run the bot."""
    try:
        # Get token (this will also log the retrieval)
        token = settings.get_token()
        
        # Create and run bot
        bot = MinimalBot()
        await bot.start(token)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        if 'bot' in locals() and not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    asyncio.run(main())