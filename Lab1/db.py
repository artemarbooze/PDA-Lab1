import re, pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, String, Integer, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert

class Base(DeclarativeBase): pass

class Car(Base):
    __tablename__ = "cars"
    listing_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(50))
    year: Mapped[int] = mapped_column(Integer)
    price: Mapped[int] = mapped_column(Integer)
    volume_l: Mapped[float | None] = mapped_column(Float)
    power_hp: Mapped[float | None] = mapped_column(Float)
    fuel: Mapped[str | None] = mapped_column(String(20))
    transmission: Mapped[str | None] = mapped_column(String(20))
    drive: Mapped[str | None] = mapped_column(String(20))
    mileage_km: Mapped[float | None] = mapped_column(Float)
    url: Mapped[str] = mapped_column(String(200))
    scraped_at: Mapped[datetime] = mapped_column(DateTime)

def prepare(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    parts = df["url"].str.extract(r"/spb/([^/]+)/([^/]+)/(\d+)\.html")
    df["brand"], df["model"], df["listing_id"] = parts[0], parts[1], parts[2].astype(int)
    df["scraped_at"] = datetime.now()
    df = df.drop(columns="name")
    return df.astype(object).where(df.notna(), None)

def load_to_db(df, engine):
    stmt = sqlite_upsert(Car)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Car.listing_id],
        set_={c: stmt.excluded[c] for c in df.columns if c != "listing_id"},
    )
    with engine.begin() as conn:
        conn.execute(stmt, df.to_dict(orient="records"))

engine = create_engine("sqlite:///drom.db")
Base.metadata.create_all(engine)
load_to_db(prepare("drom_spb.csv"), engine)