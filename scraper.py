import asyncio
import os
import re

import requests

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from utils import convert_utc_to_local
from logger import logger


load_dotenv()
url_template = os.getenv("OLX_URL")


async def get_last_n_items(city: str, n: int = 13) -> tuple[str, list[dict]]:
    url = url_template.format(city=city)

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, requests.get, url)

    response = BeautifulSoup(response.content, "html.parser")
    items = response.find_all("div", {"data-testid": "l-card"})

    links = []
    for item in items[0:n]:
        try:
            if item.select_one("[class=css-1dyfc0k]"):
                continue

            link = item.find("a").get("href")
            links.append(link)

        except Exception as e:
            logger.log(40, f"Error during scraping links: {e}")

    tasks = [loop.run_in_executor(None, requests.get, link) for link in links]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for response in responses:
        item = BeautifulSoup(response.content, "html.parser")
        try:
            try:
                title = item.find("h4", {"class": "css-1kc83jo"}).text
            except ValueError:
                title = "N/A"

            price = item.find("h3", {"data-testid": "ad-price-container"}).text.split("do negocjacji")[0]

            try:
                publication_time = item.find("span", {"data-cy": "ad-posted-at"}).text.split(" o ")[-1]
            except ValueError:
                publication_time = "N/A"

            location = item.find("p", {"class": "css-1cju8pu"}).text

            features = [item.text for item in item.findall("ul", {"class": "css-rn93um"})]

            item_link = response.url

            item_img = item.find("img")["srcset"].split(" ")[-2]

            results.append(
                {
                    "title": title,
                    "price": price,
                    "location": location,
                    "publication_time": publication_time,
                    "features": features,
                    "item_link": item_link,
                    "item_img": item_img
                }
            )
        except Exception as e:
            logger.log(40, f"Error during detailed scraping: {e}")

    return city, list(reversed(results))


async def verify_city(city: str) -> bool:
    url = url_template.format(city=city)

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, requests.get, url)

    return response.status_code == 200


if __name__ == "__main__":
    res = asyncio.run(get_last_n_items("krakow"))
    print(res)
