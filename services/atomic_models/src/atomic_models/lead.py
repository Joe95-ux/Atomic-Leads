from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from atomic_models.run import RunArtifacts

Source = Literal["google_maps"]


class BusinessLead(BaseModel):
    name: str
    website: str | None = None
    phone: str | None = None
    email: str | None = None
    city: str | None = None
    state: str | None = None
    address: str | None = None
    google_rating: float | None = None
    review_count: int | None = None
    category: str | None = None
    maps_url: str | None = None
    place_id: str | None = None
    source: Source = "google_maps"
    search_query: str = ""
    search_location: str = ""
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_csv_row(self) -> dict[str, str]:
        return {
            "name": self.name,
            "website": self.website or "",
            "phone": self.phone or "",
            "email": self.email or "",
            "city": self.city or "",
            "state": self.state or "",
            "address": self.address or "",
            "google_rating": str(self.google_rating) if self.google_rating is not None else "",
            "review_count": str(self.review_count) if self.review_count is not None else "",
            "category": self.category or "",
            "maps_url": self.maps_url or "",
            "place_id": self.place_id or "",
            "source": self.source,
            "search_query": self.search_query,
            "search_location": self.search_location,
            "scraped_at": self.scraped_at.isoformat(),
        }


class ScrapeRunMeta(BaseModel):
    query: str
    location: str
    source: Source = "google_maps"
    requested_max: int
    collected: int
    started_at: datetime
    finished_at: datetime | None = None
    artifacts: RunArtifacts | None = None
