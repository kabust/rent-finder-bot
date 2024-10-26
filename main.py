import asyncio
import os
import logging
import sys

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, html
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.utils.formatting import TextLink

from db import (
    get_user,
    write_user,
    delete_user,
    update_user_city,
    get_all_users_with_city,
)
from scraper import get_last_50_items
from utils import are_cities_similar, convert_utc_to_local


load_dotenv()


TOKEN = os.getenv("API_TOKEN")
dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


class Form(StatesGroup):
    waiting_for_first_message = State()
    waiting_for_second_message = State()


async def send_scheduled_message():
    await asyncio.sleep(10)
    while True:
        users = get_all_users_with_city()
        items = get_last_50_items()

        for user in users:
            print(f"awaiting for {user}")
            await send_items(user, items)

        await asyncio.sleep(300)


async def send_items(user: tuple, items: list) -> None:
    for item in items:
        if not are_cities_similar(user[-1], item["location"]):
            continue

        title = item["title"]
        price = item["price"]
        location = item["location"]
        publication_time = convert_utc_to_local(item["publication_time"])
        size = item["size"]
        item_link = item["item_link"]

        text = f'<strong><a href="{item_link}">{title}</a></strong>\n \
        \n{price} | {size}\n{location} - Published at {publication_time}\n'

        await bot.send_message(user[1], text)


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """
    This handler receives messages with `/start` command
    """
    user_id = message.from_user.id
    user = get_user(user_id)
    if not user:
        write_user(
            user_id,
            message.chat.id,
            message.from_user.full_name,
            message.from_user.username,
            message.from_user.is_bot,
        )

        await message.answer(
            f"Hello, {html.bold(message.from_user.first_name)}!\
            \nThis bot sends OLX rent ads every 5 minutes, so you'll have the most fresh offers out there!\
            \n\n{html.italic('Please, provide your city in polish:')}"
        )
        await state.set_state(Form.waiting_for_first_message)

    else:
        await message.answer(
            f"Hi again, {html.bold(message.from_user.first_name)}!\
            \nYour city is already set to {user[-1]}"
        )

    if not hasattr(dp, "scheduled_task"):
        print("setting scheduled task")
        dp.scheduled_task = asyncio.create_task(send_scheduled_message())


@dp.message(Form.waiting_for_first_message)
async def set_city(message: Message, state: FSMContext) -> None:
    city = message.text.capitalize()
    update_user_city(message.from_user.id, city)

    await message.answer(f"Thank you! Your city was set to {html.bold(city)}")
    await state.clear()


@dp.message()
async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
