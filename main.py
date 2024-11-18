import asyncio
import os
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from dotenv import load_dotenv

from db.user_handler import (
    get_unique_cities,
    write_user,
    get_user,
    delete_user,
    update_user_city,
    get_all_users_with_city,
)
from db.sent_ads_handler import write_ad, filter_ads, delete_old_records
from scraper import get_last_50_items, verify_city
from utils import are_cities_similar, remove_accents
from logger import logger


load_dotenv()


TOKEN = os.getenv("API_TOKEN")
dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


class Form(StatesGroup):
    waiting_for_first_message = State()
    waiting_for_second_message = State()


async def send_scheduled_message():
    while True:
        logger.log(20, f"Deleting outdated saved ads")
        delete_old_records()

        users = get_all_users_with_city()
        unique_cities = get_unique_cities()

        logger.log(
            20,
            f"Getting ads for {len(unique_cities)} cities and sending to {len(users)} users",
        )
        items = {}
        for city in unique_cities:
            items[city] = get_last_50_items(city)

        tasks = [send_items(user, items) for user in users]
        for task in asyncio.as_completed(tasks):
            try:
                await task
            except Exception as e:
                logger.log(30, e)
        # await asyncio.gather(*tasks, return_exceptions=True)

        logger.log(20, "All users were processed")
        await asyncio.sleep(300)


async def send_items(user: tuple, items: dict) -> None:
    ads_count = 0
    city = user["city"]
    for item in items[city]:
        title = item["title"]
        price = item["price"]
        location = item["location"]
        publication_time = item["publication_time"]
        size = item["size"]
        item_link = item["item_link"]

        ads_seen_by_user = filter_ads(user["user_id"])

        if item_link in ads_seen_by_user:
            continue
        else:
            write_ad(user["user_id"], item_link)
            ads_count += 1

        text = f"<strong><a href='{item_link}'>{title}</a></strong>\n \
        \n{price} | {size}\n{location} - Published at {publication_time}\n"
        await bot.send_message(user["chat_id"], text)
    logger.log(20, f"Sent {ads_count} items for user {user['user_id']}")


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """
    This handler receives messages with `/start` command
    """
    user_id = message.from_user.id
    logger.log(20, f"Received /start from user {user_id}")

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
        city = user["city"] if user["city"] else "None"
        await message.answer(
            f"Hi again, {html.bold(message.from_user.first_name)}!\
            \nYour city is already set to {city.capitalize()}\
            \n{html.italic('/update_city')}"
        )

    if not hasattr(dp, "scheduled_task"):
        logger.log(20, "Setting scheduled task")
        dp.scheduled_task = asyncio.create_task(send_scheduled_message())


@dp.message(Command("update_city"))
async def command_update_city_handler(message: Message, state: FSMContext) -> None:
    """
    This handler receives messages with `/update_city` command
    """
    await message.answer(
        f"Please, provide your city in polish:\n {html.italic('/cancel')}"
    )
    await state.set_state(Form.waiting_for_first_message)


@dp.message(Command("cancel"))
async def command_cancel_handler(message: Message, state: FSMContext) -> None:
    """
    This handler clears the state
    """
    await state.clear()


@dp.message(Form.waiting_for_first_message)
async def set_city(message: Message, state: FSMContext) -> None:
    city = message.text.capitalize()
    city_normalized = remove_accents(message.text.lower()).replace(" ", "-")

    if not verify_city(city_normalized):
        await message.answer(
            f"I couldn't set the city to {city} because it wasn't found on OLX, try again or /cancel"
        )
    else:
        update_user_city(message.from_user.id, city_normalized)
        await message.answer(
            f"Thank you! Your city was set to {html.bold(city)}, now sit back and wait for new links ;)"
        )
        await state.clear()


@dp.message()
async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
