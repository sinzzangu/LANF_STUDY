"""
Logger Setup Configuration
=========================

Professional logging setup for Discord bot with file and console output.
Supports different log levels, rotation, and formatted output.
Includes functionality to clear logs on restart.

File: setups/logger_setup.py
Author: Juan Dodam
Version: 1.0.0
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

def setup_logger(
    name: str = "discord_bot",
    log_level: str = "INFO",
    log_file: str = "logs/bot.log", 
    console_output: bool = True,
    file_output: bool = True
):
    """
    Set up comprehensive logging for the Discord bot.
    
    Args:
        name: Logger name (usually __name__ or "discord_bot")
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        console_output: Enable console logging
        file_output: Enable file logging
    
    Returns:
        logging.Logger: Configured logger instance
    """
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(levelname)s - %(message)s'
    )
    
    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Single file handler (no rotation)
    if file_output:
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Simple file handler - single file only
        file_handler = logging.FileHandler(
            filename=log_file,
            mode='w',  # 'w' mode overwrites the file on each restart
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # Log initial setup message
    logger.info(f"Logger '{name}' initialized with level {log_level}")
    logger.debug(f"Log file: {log_file}")
    logger.debug(f"Console output: {console_output}, File output: {file_output}")
    
    return logger


def log_startup_info(logger: logging.Logger):
    """
    Log useful startup information.
    
    Args:
        logger: Logger instance to use
    """
    import sys
    import discord
    import platform
    
    logger.info("=" * 50)
    logger.info("🚀 Discord Bot Starting Up")
    logger.info("=" * 50)
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"Discord.py Version: {discord.__version__}")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

def log_shutdown_info(logger: logging.Logger):
    """
    Log shutdown information.
    
    Args:
        logger: Logger instance to use
    """
    logger.info("=" * 50)
    logger.info("🛑 Discord Bot Shutting Down")
    logger.info(f"Shutdown Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

