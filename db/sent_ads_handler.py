from db.config import con, cur


def write_ad(user_id: int, olx_link: str) -> dict:
    
    ad = cur.execute(
        "INSERT INTO sent_ads(user_id, olx_link) VALUES (?, ?)",
        [user_id, olx_link],
    )

    con.commit()
    return ad.fetchone()


def filter_ads(user_id: int) -> list[dict]:
    ads = cur.execute(
        "SELECT olx_link FROM sent_ads WHERE user_id = (?)",
        [user_id]
    )
    return [ad["olx_link"] for ad in ads.fetchall()]
