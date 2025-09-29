import unicodedata
import pytz

from datetime import datetime, date, time
from difflib import SequenceMatcher

from logger import logger


def are_cities_similar(user_city: str, ad_city: str, threshold=0.8) -> bool:
    ad_city = ad_city.split(",")[0]
    similarity_ratio = SequenceMatcher(None, user_city, ad_city).ratio()
    return similarity_ratio >= threshold


def convert_utc_to_local(utc_time_str: str, local_timezone: str = "Europe/Warsaw") -> time | date:
    pl_months_map = {
        "stycznia": 1,
        "lutego": 2,
        "marca": 3,
        "kwietnia": 4,
        "maja": 5,
        "czerwca": 6,
        "lipca": 7,
        "sierpnia": 8,
        "września": 9,
        "października": 10,
        "listopada": 11,
        "grudnia": 12,
    }

    try:
        today = datetime.today()
        utc_time = datetime.strptime(utc_time_str, "%H:%M").replace(
            year=today.year, month=today.month, day=today.day, tzinfo=pytz.utc
        )

        local_time = utc_time.astimezone(pytz.timezone(local_timezone))
        return local_time.time()
    except ValueError as e:
        logger.warning(f"Failed to convert UTC time to local time: {e}, getting date instead")
        try:
            day, month_name, year = utc_time_str.split(" ")
            month = pl_months_map.get(month_name.lower())
            if month is None:
                raise ValueError(f"Unknown month name: {month_name}")
            date = datetime.strptime(f"{day}:{month}:{year}", "%d:%m:%Y")
            return date.date()
        except Exception as e:
            logger.error(f"Failed to parse date from string: {e}, returning original string")
            return utc_time_str


def remove_accents(text: str) -> str:
    # Normalize the text to separate accents from letters
    normalized_text = unicodedata.normalize("NFD", text)
    # Filter out the accent characters
    return "".join(char for char in normalized_text if unicodedata.category(char) != "Mn")
