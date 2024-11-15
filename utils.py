import unicodedata
import pytz

from datetime import datetime, date
from difflib import SequenceMatcher


def are_cities_similar(user_city: str, ad_city: str, threshold=0.8):
    ad_city = ad_city.split(",")[0]
    similarity_ratio = SequenceMatcher(None, user_city, ad_city).ratio()
    return similarity_ratio >= threshold


def convert_utc_to_local(utc_time_str, local_timezone="Europe/Warsaw"):
    today = date.today()
    utc_time = datetime.strptime(utc_time_str, "%H:%M").replace(
        year=today.year, month=today.month, day=today.day, tzinfo=pytz.utc
    )

    local_time = utc_time.astimezone(pytz.timezone(local_timezone))
    return local_time.time().strftime("%H:%M")


def remove_accents(text):
    # Normalize the text to separate accents from letters
    normalized_text = unicodedata.normalize("NFD", text)
    # Filter out the accent characters
    return "".join(
        char for char in normalized_text if unicodedata.category(char) != "Mn"
    )
