from datetime import datetime, date, timezone
from sqlalchemy import create_engine, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

DB_URL = "sqlite:///weather.db"

# Creates connection to the database
def get_engine():
    return create_engine(DB_URL, echo=False, future=True)

class Base(DeclarativeBase):
    pass

class Location(Base):
    __tablename__ = "locations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    queries: Mapped[list["Query"]] = relationship(back_populates="location")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }

class Query(Base):
    __tablename__ = "queries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    location: Mapped["Location"] = relationship(back_populates="queries")
    observations: Mapped[list["Observation"]] = relationship(
        back_populates="query", cascade="all, delete-orphan"
    )

    def to_dict(self, with_observations: bool = False):
        data = {
            "id": self.id,
            "location": self.location.to_dict() if self.location else None,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "created_at": self.created_at.isoformat(),
        }
        if with_observations:
            data["observations"] = [o.to_dict() for o in self.observations]
        return data

class Observation(Base):
    __tablename__ = "observations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    query_id: Mapped[int] = mapped_column(ForeignKey("queries.id"), nullable=False)
    query_date: Mapped[date] = mapped_column("date", Date, nullable=False)
    t_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_mean: Mapped[float | None] = mapped_column(Float, nullable=True)

    query: Mapped["Query"] = relationship(back_populates="observations")

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.query_date.isoformat(),
            "t_min": self.t_min,
            "t_max": self.t_max,
            "t_mean": self.t_mean,
        }
