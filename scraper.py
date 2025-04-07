import asyncio
import os
import requests

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from logger import logger
from utils import convert_utc_to_local

load_dotenv()
url_template = os.getenv("OLX_URL")
image_placeholder = (
    "https://archive.org/download/placeholder-image/placeholder-image.jpg"
)


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
        try:
            title = item.find("div", {"data-testid": "ad_title"}).text
        except AttributeError:
            logger.warning(f"Couldn't get title for {item_link}")
            title = "N/A"
        
        try:
            price = item.find("div", {"data-testid": "ad-price-container"}).text
        except AttributeError:
            logger.warning(f"Couldn't get price for {item_link}")
            price = "N/A"

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
                    elem.text 
                    for elem in item.find("div", {"data-testid": "qa-advert-slot"})
                    .findAllNext("p", limit=11)[:-1]
                ]
            )
        )

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

        try:
            title = item.find("h1", {"data-cy": "adPageAdTitle"}).text
        except AttributeError as e:
            logger.warning(f"Couldn't get title for {item_link}: {e}")
            title = "N/A"
        
        try:
            price = item.find("strong", {"data-cy": "adPageHeaderPrice"}).text
        except AttributeError as e:
            logger.warning(f"Couldn't get price for {item_link}: {e}")
            price = "N/A"

        try:
            location = item.find("a", {"class": "css-1jjm9oe e42rcgs1"}).text
        except AttributeError as e:
            logger.warning(f"Couldn't get location for {item_link}: {e}")
            location = "N/A"
        
        try:
            publication_time = item.find(
                "p", {"class": "e2md81j2 css-htq2ld"}
            ).text.split(" ")[-1]
        except AttributeError as e:
            logger.warning(f"Couldn't get publication_time for {item_link}: {e}")
            publication_time = "N/A"
        
        features = [
            " ".join(sub.text for sub in feature.find_all("p"))
            for feature in item.find_all("div", {"class": "css-1xw0jqp eows69w1"})
        ]

        try:
            surface = str(item.find(lambda tag: tag.name == "div" and "m²" in tag.text).string)
        except Exception as e:
            logger.warning(f"Couldn't get surface for {item_link}: {e}")
            surface = "N/A"
        
        features.append("Powierszchnia: " + surface)

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
    url = url_template.format(city=city)

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, requests.get, url)

    return response.status_code == 200


if __name__ == "__main__":
    res = asyncio.run(get_last_n_items("warszawa", 25))
    print(res)
