import asyncio
import os
import time
from typing import Literal

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from logger import logger
from utils import convert_utc_to_local


load_dotenv()
url_template = os.getenv("OLX_URL")
image_placeholder = "https://archive.org/download/placeholder-image/placeholder-image.jpg"


async def get_last_n_items(
    city: str,
    building_types: list[str] = [
        "mieszkania",
        "domy",
        "biura-lokale",
        "stancje-pokoje",
    ],
    ad_types: list[str] = ["wynajem", "sprzedaz"],
    n: int = 10,
) -> tuple[str, dict[str, dict[str, list[dict]]]]:
    loop = asyncio.get_event_loop()
    start_time = time.time()

    url_tasks = [
        loop.run_in_executor(
            None,
            lambda url: requests.get(url),
            url_template.format(city=city, building_type=building_type, ad_type=ad_type),
        )
        for building_type in building_types
        for ad_type in ad_types
    ]
    url_responses = await asyncio.gather(*url_tasks, return_exceptions=True)

    items = {}
    for i, ad_type in enumerate(ad_types):
        items[ad_type] = {}
        for j, building_type in enumerate(building_types):
            items[ad_type][building_type] = BeautifulSoup(
                url_responses[i + j].content, "html.parser"
            ).select("div[data-testid='l-card']:not([style*='display: none !important'])")

    links = {}
    for ad_type in ad_types:
        links[ad_type] = {}
        for building_type in building_types:
            links[ad_type][building_type] = []
            for item in items[ad_type][building_type][: n + 1]:
                try:
                    if item.select_one("[class=css-1dyfc0k]"):
                        continue

                    item_url = item.find("a").get("href")
                    link = (
                        f"https://olx.pl/{item_url}"
                        if not item_url.startswith("https://www.otodom.pl")
                        else item_url
                    )
                    links[ad_type][building_type].append(link)

                except Exception as e:
                    logger.exception(f"Error during scraping links: {e}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    }

    item_tasks = {}
    for ad_type in ad_types:
        item_tasks[ad_type] = {}
        for building_type in building_types:
            item_tasks[ad_type][building_type] = [
                loop.run_in_executor(None, lambda x: requests.get(x, headers=headers), link)
                for link in links[ad_type][building_type]
            ]

    item_responses = {}
    for ad_type in ad_types:
        item_responses[ad_type] = {}
        for building_type in building_types:
            item_responses[ad_type][building_type] = await asyncio.gather(
                *item_tasks[ad_type][building_type], return_exceptions=True
            )

    end_time = time.time()
    logger.info(f"Scraping took: {end_time - start_time} seconds")

    start_time = time.time()
    results = {}
    for ad_type in ad_types:
        results[ad_type] = {}
        for building_type in building_types:
            results[ad_type][building_type] = []
            for response in item_responses[ad_type][building_type]:
                item_url = response.url
                if item_url.startswith("https://www.olx.pl"):
                    parsed_item = parse_olx(response)
                    results[ad_type][building_type].append(parsed_item)
                elif item_url.startswith("https://www.otodom.pl"):
                    parsed_item = parse_otodom(response)
                    results[ad_type][building_type].append(parsed_item)
                else:
                    logger.exception(f"Couldn't parse {item_url}")
            results[ad_type][building_type] = list(reversed(results[ad_type][building_type]))

    end_time = time.time()
    logger.info(f"Parsing took: {end_time - start_time} seconds")

    return city, results


def parse_olx(response: requests.Response) -> dict:
    item = BeautifulSoup(response.content, "html.parser")
    try:
        item_link = response.url
        title = item.find("div", {"data-cy": "offer_title"}).text
        price = (
            item.find("div", {"data-testid": "ad-price-container"})
            .text.lower()
            .split(" do negocjacji")[0]
        )

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

        features = list(
            reversed(
                [
                    item.text
                    for item in (
                        item.find("div", {"data-testid": "ad-parameters-container"}).find_all("p")[
                            :-1
                        ]
                    )
                ]
            )
        )

        try:
            item_img = item.find("img", {"class": "css-1bmvjcs"})["srcset"].split(" ")[-2]
        except (KeyError, TypeError):
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
        logger.exception(f"Error during detailed OLX parsing: {e}, item URL: {response.url}")


def parse_otodom(response: requests.Response) -> dict:
    item = BeautifulSoup(response.content, "html.parser")
    try:
        item_link = response.url
        title = item.find("h1", {"data-cy": "adPageAdTitle"}).text
        price = item.find("strong", {"data-cy": "adPageHeaderPrice"}).text
        location = item.find("div", {"data-sentry-component": "MapLink"}).find("a").text
        publication_time = (
            item.find("div", {"data-sentry-component": "AdHistoryBase"})
            .find("p")
            .text.split(" ")[-1]
        )
        features = [
            " ".join(sub.text for sub in feature.find_all("div"))
            for feature in (
                item.find("div", {"data-sentry-component": "AdDetailsBase"})
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
        logger.exception(f"Error during detailed Otodom parsing: {e}, item URL: {response.url}")


async def verify_city(city: str) -> bool:
    url = url_template.format(city=city, building_type="mieszkania", ad_type="wynajem")

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, requests.get, url)

    return response.status_code == 200


if __name__ == "__main__":
    res = asyncio.run(get_last_n_items("warszawa", 25))
    print(res)
