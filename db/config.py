from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, DateTime
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime


DATABASE_URL = "sqlite:///db.sqlite"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, nullable=False)
    chat_id = Column(Integer, nullable=False)
    full_name = Column(String(50))
    username = Column(String(50))
    is_bot = Column(Boolean)
    city = Column(String(50))
    is_active = Column(Boolean, nullable=False, default=True)
    building_type_filter = Column(String(50), nullable=True, default="mieszkania")
    ad_type_filter = Column(String(50), nullable=True, default="wynajem")
    min_price_filter = Column(Integer, nullable=True)
    max_price_filter = Column(Integer, nullable=True)
    min_surface_area_filter = Column(Integer, nullable=True)


class SentAd(Base):
    __tablename__ = "sent_ads"
    id = Column(Integer, primary_key=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, nullable=False)
    olx_link = Column(String, nullable=False)


# Create tables (for development only; use Alembic for migrations in production)
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
