"""
Bot Settings Configuration File
This file contains the settings for the bot.

Author: Juan Dodam
Version: 2.0.0 - Updated for Slash Commands
"""
import discord
import os
from dotenv import load_dotenv
from setups.logger_setup import setup_logger, log_startup_info, log_shutdown_info
load_dotenv()

# Bot Description
BOT_DESCRIPTION = "Sample Discord Bot with Slash Commands, created by Juan Dodam"

# Bot Version
BOT_VERSION = "2.0.0"

# Bot Author
BOT_AUTHOR = "Juan Dodam"

AUTO_LOAD_COGS = True

# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Log file path
LOG_FILE = 'logs/bot.log'

# Enable console logging
CONSOLE_LOGGING = True

# Enable file logging
FILE_LOGGING = True


def get_intents():
    """
    Configure Discord intents based on bot requirements

    Returns:
        discord.Intents: Configured discord intents object
    """
    intents = discord.Intents.default() # default intents
    intents.message_content = True # enable message content intent
    intents.members = True # enable members intent
    intents.guilds = True # enable guilds intent
    intents.reactions = True # enable reactions intent
    # intents.presences = True # enable presences intent
    # intents.typing = True # enable typing intent
    intents.voice_states = True # enable voice states intent
    intents.dm_messages = True # enable dm messages intent
    intents.dm_reactions = True # enable dm reactions intent
    intents.dm_typing = True # enable dm typing intent

    return intents

def get_configured_logger():
    """
    Get a fully configured logger for the bot.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = setup_logger(
        name="discord_bot",
        log_level=LOG_LEVEL,
        log_file=LOG_FILE,
        console_output=CONSOLE_LOGGING,
        file_output=FILE_LOGGING
    )
    
    return logger

def get_token():
    """
    Get the bot token from environment variables.
    
    Returns:
        str: Bot token
    """
    logger = get_configured_logger()
    
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("❌ DISCORD_BOT_TOKEN not found in environment variables")
        raise ValueError("DISCORD_BOT_TOKEN not found in environment variables")
    
    # Validate token format
    if len(token) < 50:
        logger.warning("⚠️ Token appears to be unusually short - may be invalid")
    
    logger.info("✅ Discord bot token retrieved and validated successfully")
    
    return token


def log_bot_startup(logger):
    """
    Log bot startup information.
    
    Args:
        logger: Logger instance
    """
    log_startup_info(logger)


def log_bot_shutdown(logger):
    """
    Log bot shutdown information.
    
    Args:
        logger: Logger instance
    """
    log_shutdown_info(logger)