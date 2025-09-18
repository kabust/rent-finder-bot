import asyncio
import os
import requests
from typing import Literal

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from logger import logger
from utils import convert_utc_to_local


load_dotenv()
url_template = os.getenv("OLX_URL")
image_placeholder = (
    "https://archive.org/download/placeholder-image/placeholder-image.jpg"
)


async def get_last_n_items(
        city: str,
        building_types: list[str] = ["mieszkania", "domy"],
        ad_types: list[str] = ["wynajem", "sprzedaz"],
        n: int = 20
    ) -> tuple[str, list[dict]]:
    items = []

    for ad_type in ad_types:
        for building_type in building_types:
            url = url_template.format(
                city=city, 
                building_type=building_type, 
                ad_type=ad_type
            )
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, requests.get, url)

            response = BeautifulSoup(response.content, "html.parser")
            items.extend(response.find_all("div", {"data-testid": "l-card"}))

    links = []
    for item in items[:n + 1]:
        try:
            if item.select_one("[class=css-1dyfc0k]"):
                continue

            item_url = item.find("a").get("href")
            link = (
                f"https://olx.pl/{item_url}"
                if not item_url.startswith("https://www.otodom.pl")
                else item_url
            )
            links.append(link)

        except Exception as e:
            logger.exception(f"Error during scraping links: {e}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    }
    tasks = [
        loop.run_in_executor(None, lambda x: requests.get(x, headers=headers), link)
        for link in links
    ]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for response in responses:
        item_url = response.url
        if item_url.startswith("https://www.olx.pl"):
            parsed_item = parse_olx(response)
            results.append(parsed_item)
        elif item_url.startswith("https://www.otodom.pl"):
            parsed_item = parse_otodom(response)
            results.append(parsed_item)
        else:
            logger.exception(f"Couldn't parse {item_url}")

    return city, list(reversed(results))


def parse_olx(response: requests.Response) -> dict:
    item = BeautifulSoup(response.content, "html.parser")
    try:
        item_link = response.url
        title = item.find("div", {"data-cy": "offer_title"}).text
        price = item.find("div", {"data-testid": "ad-price-container"}).text.lower().split(" do negocjacji")[0]

        try:
            publication_time = convert_utc_to_local(
                item.find("span", {"data-cy": "ad-posted-at"}).text.split(" o ")[-1]
            )
        except AttributeError:
            logger.warning(f"Couldn't get publication_time for {item_link}")
            publication_time = "N/A"

        location = ", ".join(
            "".join(i.a.text.split(" - ")[-1])
            for i in item.find_all("li", {"data-testid": "breadcrumb-item"})[-2:]
        )

        features = list(reversed(
                [
                    item.text 
                    for item in (
                        item
                        .find("div", {"data-testid": "ad-parameters-container"})
                        .find_all("p")[:-1]
                    )
                ]
            ))

        try:
            item_img = item.find("img", {"class": "css-1bmvjcs"})["srcset"].split(" ")[-2]
        except KeyError:
            logger.warning(f"Couldn't get image for {item_link}")
            item_img = image_placeholder

        return {
            "title": title,
            "price": price,
            "location": location,
            "publication_time": publication_time,
            "features": features,
            "item_link": item_link,
            "item_img": item_img,
        }

    except Exception as e:
        logger.exception(
            f"Error during detailed OLX parsing: {e}, item URL: {response.url}"
        )


def parse_otodom(response: requests.Response) -> dict:
    item = BeautifulSoup(response.content, "html.parser")
    try:
        item_link = response.url
        title = item.find("h1", {"data-cy": "adPageAdTitle"}).text
        price = item.find("strong", {"data-cy": "adPageHeaderPrice"}).text
        location = item.find("div", {"data-sentry-component": "MapLink"}).find("a").text
        publication_time = item.find(
            "div", {"data-sentry-component": "AdHistoryBase"}
        ).find("p").text.split(" ")[-1]
        features = [
            " ".join(sub.text for sub in feature.find_all("div"))
            for feature in (
                item
                .find("div", {"data-sentry-component": "AdDetailsBase"})
                .find("div")
                .find_all("div", {"data-sentry-element": "ItemGridContainer"})
            )
        ]

        try:
            item_img = item.find("picture").find_next("img")["src"]
        except Exception as e:
            logger.warning(f"Couldn't get image for {item_link}: {e}")
            item_img = image_placeholder

        return {
            "title": title,
            "price": price,
            "location": location,
            "publication_time": publication_time,
            "features": features,
            "item_link": item_link,
            "item_img": item_img,
        }

    except Exception as e:
        logger.exception(
            f"Error during detailed Otodom parsing: {e}, item URL: {response.url}"
        )


async def verify_city(city: str) -> bool:
    url = url_template.format(city=city, building_type="mieszkania", ad_type="wynajem")

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, requests.get, url)

    return response.status_code == 200


if __name__ == "__main__":
    res = asyncio.run(get_last_n_items("warszawa", 25))
    print(res)
