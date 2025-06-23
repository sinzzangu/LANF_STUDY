import asyncio
import settings
from bot import SlashBot
import utils.riot_api as riot_api

async def main():
    """Run the bot."""
    try:
        # Get token (this will also log the retrieval)
        token = settings.get_token() #discord
        key = settings.get_riot_api_key() #riot

        # Set API key before creating bot
        riot_api.set_api_key(key)

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