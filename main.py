import asyncio
import settings
from bot import SlashBot

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