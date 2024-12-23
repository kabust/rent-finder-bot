import asyncio
import os

from aiogram import Bot, Dispatcher, html
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from db.user_handler import (
    get_unique_cities,
    write_user,
    get_user,
    delete_user,
    update_user_city,
    get_all_active_users_with_city,
    activate_user,
    deactivate_user, get_all_users
)
from db.sent_ads_handler import write_ad, filter_ads, delete_old_records
from scraper import get_last_n_items, verify_city
from utils import are_cities_similar, remove_accents
from logger import logger


load_dotenv()

TOKEN = os.getenv("API_TOKEN")
dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


class Form(StatesGroup):
    waiting_for_city = State()
    waiting_for_admin_message = State()


async def send_scheduled_message():
    while True:
        logger.info(f"Deleting outdated saved ads")
        delete_old_records()

        users = get_all_active_users_with_city()
        unique_cities = get_unique_cities()

        logger.info(f"Getting ads for {len(unique_cities)} cities and sending to {len(users)} users")
        items = {}
        tasks = [get_last_n_items(city) for city in unique_cities]
        for task in asyncio.as_completed(tasks):
            try:
                city, result = await task
                items[city] = result
            except Exception as e:
                logger.exception(f"Error during requesting: {e}")

        tasks = [send_items(user, items) for user in users]
        for task in asyncio.as_completed(tasks):
            try:
                await task
            except Exception as e:
                logger.warning(e)

        logger.info("All users were processed")
        await asyncio.sleep(180)


async def send_items(user: dict, items: dict) -> None:
    ads_count = 0
    city = user["city"]
    for item in items.get(city):
        title = item["title"]
        price = item["price"]
        location = item["location"][:40] + "..." if len(item["location"]) > 40 else item["location"]
        publication_time = item["publication_time"]
        features = "".join(f"▫️ {feature}\n" for feature in item["features"])
        item_link = item["item_link"]
        item_img = item["item_img"]

        ads_seen_by_user = filter_ads(user["user_id"])

        if item_link in ads_seen_by_user:
            continue
        else:
            text = f"<strong><a href='{item_link}'>{title}</a></strong>\n \
            \n{price} | {location}\nPublished: {publication_time}\n \
            \nFeatures: \n{features}"

            await bot.send_photo(
                chat_id=user["chat_id"],
                photo=item_img,
                caption=text
            )
            write_ad(user["user_id"], item_link)
            ads_count += 1
    logger.info(f"Sent {ads_count} items for user {user['user_id']}")


@dp.message(CommandStart())
async def command_start_handler(
        message: Message, state: FSMContext, user_id: int = None
) -> None:
    """
    This handler receives messages with `/start` command
    """
    inline_kb = InlineKeyboardBuilder()
    inline_kb.button(text="Update city", callback_data="update_city")

    reply_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Update City"), KeyboardButton(text="Pause")],
            [KeyboardButton(text="Filters")],
        ],
        resize_keyboard=True
    )

    if not user_id:
        user_id = message.from_user.id
    logger.info(f"Received /start from user {user_id}")

    await message.answer("Menu keyboard added, check it out!", reply_markup=reply_kb)

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
            \nThis bot checks for new OLX rent ads every minute, so you'll have the most fresh offers out there!\
            \n\n{html.italic('Please, provide your city in polish:')}",
        )
        await state.set_state(Form.waiting_for_city)

    else:
        activate_user(user_id)
        city = user["city"] if user["city"] else "None"
        await message.answer(
            f"Hi again, {html.bold(user['full_name'])}!\
            \nYour city is already set to {city.capitalize()}",
            reply_markup=inline_kb.as_markup()
        )

    if not hasattr(dp, "scheduled_task"):
        logger.info("Setting scheduled task")
        dp.scheduled_task = asyncio.create_task(send_scheduled_message())


@dp.message(Command("update_city"))
async def command_update_city_handler(
        message: Message, state: FSMContext, user_id: int = None
) -> None:
    """
    This handler receives messages with `/update_city` command
    """
    inline_kb = InlineKeyboardBuilder()
    inline_kb.button(text="Cancel", callback_data="cancel")

    logger.info(f"Received /update_city from user {user_id}")

    await message.answer(
        f"Please, provide your city in polish",
        reply_markup=inline_kb.as_markup(),
    )

    await state.set_state(Form.waiting_for_city)


@dp.message(Command("pause"))
async def command_pause_handler(message: Message) -> None:
    """
    This handler clears the state
    """
    inline_kb = InlineKeyboardBuilder()
    inline_kb.button(text="Start to resume", callback_data="start")

    user_id = message.from_user.id
    deactivate_user(user_id)
    logger.info(f"Received /pause from user {user_id}")
    await message.answer("Bot is paused", reply_markup=inline_kb.as_markup())


@dp.message(Command("admin_message"))
async def send_message_by_admin(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    if user_id == 405433809:
        await message.answer("Write message for all users")
        await state.set_state(Form.waiting_for_admin_message)


@dp.message(Form.waiting_for_admin_message)
async def send_message_to_users(message: Message, state: FSMContext):
    users = get_all_users()
    tasks = [bot.send_message(user["chat_id"], message.text) for user in users]
    await asyncio.gather(*tasks)
    await message.answer("Message sent successfully")
    await state.clear()


@dp.message(Form.waiting_for_city)
async def set_city(message: Message, state: FSMContext) -> None:
    inline_kb = InlineKeyboardBuilder()
    inline_kb.button(text="Cancel", callback_data="cancel")

    city = message.text.capitalize()
    city_normalized = remove_accents(message.text.lower()).replace(" ", "-")

    is_city_valid = await verify_city(city_normalized)
    if not is_city_valid:
        await message.answer(
            f"I couldn't set the city to {city} because it wasn't found on OLX, try again",
            reply_markup=inline_kb.as_markup()
        )
    else:
        update_user_city(message.from_user.id, city_normalized)
        await message.answer(
            f"Thank you! Your city was set to {html.bold(city)}, now sit back and wait for new links ;)"
        )
        await state.clear()


@dp.callback_query()
async def handle_callback_query(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if callback.data == "update_city":
        await command_update_city_handler(callback.message, state, user_id)
        await callback.message.delete()
    elif callback.data == "cancel":
        await state.clear()
        await callback.message.delete()
        await callback.answer("Action cancelled")
    elif callback.data == "start":
        await command_start_handler(callback.message, state, user_id)
        await callback.message.delete()

    await callback.answer()


@dp.message()
async def handle_reply(message: Message, state: FSMContext):
    if message.text == "Update City":
        await command_update_city_handler(message, state)
    elif message.text == "Pause":
        await command_pause_handler(message)
    elif message.text == "Filters":
        await message.answer("<i>Will be available soon</i>")
    else:
        await message.answer("Please choose a valid option from the keyboard menu")


@dp.message()
async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
