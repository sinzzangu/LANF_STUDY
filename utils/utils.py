"""
Bot Utility Functions
====================
All bot utility functions and helper methods.

Author: Juan Dodam
Version: 3.0.0 - Modular Structure
"""

import discord
from discord import app_commands
from pathlib import Path
import importlib
import settings


def initialize_bot(bot):
    """Initialize bot with settings and logger."""
    # Set up logger first
    bot.logger = settings.get_configured_logger()
    
    # Log startup info
    settings.log_bot_startup(bot.logger)
    
    # Initialize parent class
    discord.Client.__init__(
        bot,
        intents=settings.get_intents(),
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="for slash commands"
        )
    )
    
    # Initialize command tree
    bot.tree = app_commands.CommandTree(bot)


async def setup_bot(bot):
    """Load all cogs and sync commands on startup."""
    if settings.AUTO_LOAD_COGS:
        await load_all_cogs(bot)
    
    # Debug: Show loaded commands
    commands = bot.tree.get_commands()
    bot.logger.info(f"📋 Loaded commands: {[cmd.name for cmd in commands]}")
    
    # Sync commands to Discord
    try:
        synced = await bot.tree.sync()
        bot.logger.info(f"🔄 Synced {len(synced)} slash commands")
        bot.logger.info(f"📤 Synced command names: {[cmd.name for cmd in synced]}")
    except Exception as e:
        bot.logger.error(f"❌ Failed to sync commands: {e}")
        # Print more detailed error
        import traceback
        bot.logger.error(f"Full error: {traceback.format_exc()}")


async def load_all_cogs(bot):
    """Load all cog files from the cogs directory and subdirectories."""
    cogs_dir = Path("cogs")
    
    if not cogs_dir.exists():
        bot.logger.warning(f"Cogs directory not found: {cogs_dir}")
        return
    
    loaded = 0
    
    # Load cogs from subdirectories (lol, pubg, utils, valorant, etc.)
    for category_dir in cogs_dir.iterdir():
        if category_dir.is_dir() and not category_dir.name.startswith('_'):
            loaded += await load_cogs_from_directory(bot, category_dir)
    
    # Also load any cogs directly in the cogs directory
    for cog_file in cogs_dir.glob("*.py"):
        if not cog_file.name.startswith("_"):
            loaded += await load_single_cog(bot, f"cogs.{cog_file.stem}")
    
    bot.logger.info(f"📦 Loaded {loaded} cogs total")


async def load_cogs_from_directory(bot, directory):
    """Load all cogs from a specific directory."""
    loaded = 0
    category = directory.name
    
    for cog_file in directory.glob("*.py"):
        if not cog_file.name.startswith("_"):
            # Create module path: cogs.pubg.secretroom
            module_path = f"cogs.{category}.{cog_file.stem}"
            if await load_single_cog(bot, module_path):
                loaded += 1
    
    if loaded > 0:
        bot.logger.info(f"📁 Loaded {loaded} cogs from {category} category")
    
    return loaded


async def load_single_cog(bot, module_path):
    """Load a single cog from module path."""
    try:
        # Dynamic import
        module = importlib.import_module(module_path)
        
        if hasattr(module, 'setup'):
            await module.setup(bot)
            bot.logger.info(f"✅ Loaded cog: {module_path}")
            return True
        else:
            bot.logger.warning(f"⚠️ No setup function found in {module_path}")
            return False
            
    except Exception as e:
        bot.logger.error(f"❌ Failed to load cog {module_path}: {e}")
        return False


async def on_bot_ready(bot):
    """Handle bot ready event."""
    bot.logger.info(f"🚀 {bot.user} is online!")
    bot.logger.info(f"📊 Connected to {len(bot.guilds)} guilds")
    bot.logger.info(f"⚡ Using slash commands")
    
    # Update presence to show slash command usage
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="for slash commands | /help"
    )
    await bot.change_presence(activity=activity)


async def handle_command_error(bot, interaction, error):
    """Handle slash command errors."""
    bot.logger.error(f"❌ SLASH COMMAND ERROR OCCURRED!")
    bot.logger.error(f"Command: {interaction.command.name if interaction.command else 'Unknown'}")
    bot.logger.error(f"User: {interaction.user}")
    bot.logger.error(f"Guild: {interaction.guild.name if interaction.guild else 'DM'}")
    bot.logger.error(f"Error Type: {type(error).__name__}")
    bot.logger.error(f"Error Message: {str(error)}")
    
    # Full traceback
    import traceback
    bot.logger.error(f"Full traceback: {traceback.format_exc()}")
    
    # Try to respond if we haven't already
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"❌ 명령어 실행 중 오류가 발생했습니다: {str(error)}", 
                ephemeral=True
            )
            bot.logger.info("✅ Error response sent to user")
        else:
            await interaction.edit_original_response(
                content=f"❌ 명령어 실행 중 오류가 발생했습니다: {str(error)}"
            )
            bot.logger.info("✅ Error response edited")
    except Exception as response_error:
        bot.logger.error(f"❌ Failed to send error response: {response_error}")


async def log_interaction(bot, interaction):
    """Log all interactions."""
    if interaction.type == discord.InteractionType.application_command:
        bot.logger.info(f"🎯 INTERACTION RECEIVED: /{interaction.command.name} from {interaction.user}")


async def handle_guild_join(bot, guild):
    """Handle guild join event - sync commands."""
    try:
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        bot.logger.info(f"📥 Joined guild '{guild.name}' and synced commands")
    except Exception as e:
        bot.logger.error(f"❌ Failed to sync commands for guild '{guild.name}': {e}")


async def handle_bot_shutdown(bot):
    """Handle bot shutdown."""
    settings.log_bot_shutdown(bot.logger)


# Helper function for command registration
def register_command(bot, command_func):
    """Helper function to register a command to the bot tree."""
    bot.tree.add_command(command_func)
    return command_func