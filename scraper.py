import os
import re

import requests

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from utils import convert_utc_to_local
from logger import logger


load_dotenv()
url_template = os.getenv("OLX_URL")


def get_last_5_items(city: str) -> list[dict]:
    url = url_template.format(city=city)
    response = requests.get(url)
    response = BeautifulSoup(response.content, "html.parser")
    items = response.find_all("div", {"data-testid": "l-card"})

    results = []
    for item in items[0:5]:
        try:
            if item.select_one("[class=css-1dyfc0k]"):
                continue

            try:
                title = item.find("h4", {"class": "css-1s3qyje"}).text
            except ValueError:
                title = "N/A"

            price = item.find("p", {"data-testid": "ad-price"}).text.split("do negocjacji")[0]

            location, publication_time = item.find("p", {"data-testid": "location-date"}).text.split(" - ")
            try:
                publication_time = convert_utc_to_local(re.split(' o |, ', publication_time)[-1])
            except ValueError:
                publication_time = "N/A"

            size = item.find("span", {"class": "css-1cd0guq"}).text

            item_link = item.find("a")["href"]
            item_link = (
                f"https://olx.pl{item_link}" if not "https:" in item_link else item_link
            )

            item_img = item.find("img")["srcset"].split(" ")[-2]

            results.append(
                {
                    "title": title,
                    "price": price,
                    "location": location,
                    "publication_time": publication_time,
                    "size": size,
                    "item_link": item_link,
                    "item_img": item_img
                }
            )
        except Exception as e:
            logger.log(40, f"Error during scraping: {e}")

    return list(reversed(results))


def verify_city(city: str) -> bool:
    url = url_template.format(city=city)
    response = requests.get(url)
    return response.status_code == 200


if __name__ == "__main__":
    print(get_last_5_items("krakow")[0])
