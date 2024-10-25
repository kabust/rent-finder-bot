import asyncio
import os
import logging
import sys

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.formatting import TextLink

from db import get_user, write_user, delete_user, update_user_city
from scraper import get_last_50_items

load_dotenv()


TOKEN = os.getenv("API_TOKEN")
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    user_id = message.from_user.id
    user = get_user(user_id)
    print(user)
    if not user:
        write_user(
            user_id,
            message.from_user.full_name,
            message.from_user.username,
            message.from_user.is_bot,
        )

    await message.answer(f"Hello, {html.bold(message.from_user.id)}!")


@dp.message(Command("ads"))
async def send_items(message: Message) -> None:
    ads = get_last_50_items()
    
    for ad in ads:
        title = ad["title"]
        price = ad["price"]
        location = ad["location"]
        publication_time = ad["publication_time"]
        size = ad["size"]
        image_link = ad["image_link"]
        item_link = ad["item_link"]

        text = f"{TextLink(title, url=item_link)} - {price}\n{location}"
        await message.answer(text)


@dp.message()
async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
