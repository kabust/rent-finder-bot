from calendar import month
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from db.config import con, cur


def write_ad(user_id: int, olx_link: str) -> dict:
    ad = cur.execute(
        "INSERT INTO sent_ads(user_id, olx_link) VALUES (?, ?)",
        [user_id, olx_link],
    )

    con.commit()
    return ad.fetchone()


def filter_ads(user_id: int) -> list[dict]:
    ads = cur.execute("SELECT olx_link FROM sent_ads WHERE user_id = (?)", [user_id])
    return [ad["olx_link"] for ad in ads.fetchall()]


def delete_old_records() -> None:
    timestamp_threshold = (
        datetime.now(tz=timezone.utc) - relativedelta(months=1)
    ).strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("DELETE FROM sent_ads WHERE timestamp < (?)", [timestamp_threshold])
    con.commit()


if __name__ == "__main__":
    delete_old_records()
