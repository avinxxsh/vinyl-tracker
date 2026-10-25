from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    artist = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    label = Column(String, nullable=True)
    genre = Column(String, nullable=True, index=True)
    pressing_year = Column(Integer, nullable=True)
    condition = Column(String, nullable=True)
    sleeve_condition = Column(String, nullable=True)
    purchase_price = Column(Float, nullable=True)
    discogs_release_id = Column(Integer, nullable=True, index=True)
    cover_url = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    date_added = Column(String, nullable=True)
    status = Column(String, nullable=False, server_default="owned", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=True)
