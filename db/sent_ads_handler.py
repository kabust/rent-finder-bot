from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

from db.config import SessionLocal, SentAd


def write_ad(user_id: int, olx_link: str) -> SentAd:
    session = SessionLocal()
    ad = SentAd(user_id=user_id, olx_link=olx_link)
    session.add(ad)
    session.commit()
    session.refresh(ad)
    session.close()
    return ad


def filter_ads(user_id: int) -> list[str]:
    session = SessionLocal()
    ads = session.query(SentAd).filter(SentAd.user_id == user_id).all()
    session.close()
    return [ad.olx_link for ad in ads]


def delete_old_records() -> None:
    session = SessionLocal()
    timestamp_threshold = datetime.now(tz=timezone.utc) - relativedelta(months=1)
    session.query(SentAd).filter(SentAd.timestamp < timestamp_threshold).delete()
    session.commit()
    session.close()


if __name__ == "__main__":
    delete_old_records()
