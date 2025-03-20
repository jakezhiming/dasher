import asyncio
from src.utils.compat import IS_WEB

if not IS_WEB:
    from dotenv import load_dotenv

    load_dotenv()

from src.core.game import Game
from src.utils.logger import logger, get_module_logger

logger = get_module_logger("main")


async def main():
    game = Game()
    await game.run()


logger.info("Starting game")
try:
    if IS_WEB:
        # In web environment, use the existing event loop instead of creating a new one
        loop = asyncio.get_event_loop()
        loop.create_task(main())
    else:
        # In desktop environment, use asyncio.run
        asyncio.run(main())
except Exception as e:
    logger.error(f"Failed to start game: {str(e)}", exc_info=True)
    if not IS_WEB:
        exit()
