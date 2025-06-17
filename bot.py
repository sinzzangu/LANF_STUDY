#!/usr/bin/env python3
"""
Discord Bot with Slash Commands
==============================
Discord bot using slash commands instead of prefix commands.
All functionality is handled by cogs loaded from the cogs directory.
All configuration is handled by settings.py.

Author: Juan Dodam
Version: 2.0.0 - Updated for Slash Commands
"""

import asyncio
from pathlib import Path

import discord
from discord import app_commands

# Import bot settings
import settings

class SlashBot(discord.Client):
    """Discord bot that uses slash commands exclusively."""
    
    def __init__(self):
        """Initialize bot using settings from settings.py."""
        # Set up logger first
        self.logger = settings.get_configured_logger()
        
        # Log startup info
        settings.log_bot_startup(self.logger)
        
        super().__init__(
            intents=settings.get_intents(),
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for slash commands"
            )
        )
        
        # Initialize command tree
        self.tree = app_commands.CommandTree(self) # creating an empty tree
    
    async def setup_hook(self):
        """Load all cogs and sync commands on startup."""
        if settings.AUTO_LOAD_COGS:
            await self.load_all_cogs()
        
        
        # Sync commands to Discord
        try:
            synced = await self.tree.sync()
            self.logger.info(f"🔄 Synced {len(synced)} slash commands")
            self.logger.info(f"📤 Synced command names: {[cmd.name for cmd in synced]}")
        except Exception as e:
            self.logger.error(f"❌ Failed to sync commands: {e}")
            # Print more detailed error
            import traceback
            self.logger.error(f"Full error: {traceback.format_exc()}")
    
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
            
            cog_name = f"cogs.{cog_file.stem}"
            

            try:
                # Import the module and call setup function
                module = __import__(cog_name, fromlist=[''])
                if hasattr(module, 'setup'):
                    await module.setup(self)
                    self.logger.info(f"✅ Loaded cog: {cog_name}")
                    loaded += 1
                else:
                    self.logger.warning(f"⚠️ No setup function found in {cog_name}")
            except Exception as e:
                self.logger.error(f"❌ Failed to load cog {cog_name}: {e}")
        
        self.logger.info(f"📦 Loaded {loaded} cogs total")
    
    async def on_ready(self):
        """Bot ready event."""
        self.logger.info(f"🚀 {self.user} is online!")
        self.logger.info(f"📊 Connected to {len(self.guilds)} guilds")
        self.logger.info(f"⚡ Using slash commands")
        
        # Update presence to show slash command usage
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for slash commands | /help"
        )
        await self.change_presence(activity=activity)
    
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle slash command errors."""
        self.logger.error(f"❌ SLASH COMMAND ERROR OCCURRED!")
        self.logger.error(f"Command: {interaction.command.name if interaction.command else 'Unknown'}")
        self.logger.error(f"User: {interaction.user}")
        self.logger.error(f"Guild: {interaction.guild.name if interaction.guild else 'DM'}")
        self.logger.error(f"Error Type: {type(error).__name__}")
        self.logger.error(f"Error Message: {str(error)}")
        
        # Full traceback
        import traceback
        self.logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Try to respond if we haven't already
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ 명령어 실행 중 오류가 발생했습니다: {str(error)}", 
                    ephemeral=True
                )
                self.logger.info("✅ Error response sent to user")
            else:
                await interaction.edit_original_response(
                    content=f"❌ 명령어 실행 중 오류가 발생했습니다: {str(error)}"
                )
                self.logger.info("✅ Error response edited")
        except Exception as response_error:
            self.logger.error(f"❌ Failed to send error response: {response_error}")
    
    async def on_interaction(self, interaction: discord.Interaction):
        """Log all interactions."""
        if interaction.type == discord.InteractionType.application_command:
            self.logger.info(f"🎯 INTERACTION RECEIVED: /{interaction.command.name} from {interaction.user}")
        await super().on_interaction(interaction)
    
    async def on_guild_join(self, guild):
        """Sync commands when joining a new guild."""
        try:
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            self.logger.info(f"📥 Joined guild '{guild.name}' and synced commands")
        except Exception as e:
            self.logger.error(f"❌ Failed to sync commands for guild '{guild.name}': {e}")
    
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
        bot = SlashBot()
        await bot.start(token)
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        if 'bot' in locals() and not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    asyncio.run(main())