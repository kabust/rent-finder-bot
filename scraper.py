import os
import requests

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from utils import convert_utc_to_local

load_dotenv()

url_template = os.getenv("OLX_URL")


def get_last_50_items(city: str) -> list[dict]:
    url = url_template.replace("{{city}}", city)
    response = requests.get(url)
    response = BeautifulSoup(response.content, "html.parser")
    items = response.find_all("div", {"data-testid": "l-card"})

    results = []
    for item in items[0:50]:
        if item.select_one("[class=css-1dyfc0k]"):
            continue

        title = item.find("h6", {"class": "css-1wxaaza"}).text
        price = item.find("p", {"class": "css-13afqrm"}).text.split("do negocjacji")[0]

        location, publication_time = item.find("p", {"data-testid": "location-date"}).text.split(" - ")
        publication_time = convert_utc_to_local(publication_time.split(" o ")[-1])

        size = item.find("span", {"class": "css-1cd0guq"}).text

        item_link = item.find("a")["href"]
        item_link = (
            f"https://olx.pl{item_link}" if not "https:" in item_link else item_link
        )

        results.append(
            {
                "title": title,
                "price": price,
                "location": location,
                "publication_time": publication_time,
                "size": size,
                "item_link": item_link,
            }
        )

    return list(reversed(results))


def verify_city(city: str) -> bool:
    url = url_template.replace("{{city}}", city)
    response = requests.get(url)
    return response.status_code == 200
