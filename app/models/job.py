from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, HttpUrl


class ATSProvider(str, Enum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"


class RawJob(BaseModel):
    """Raw job data as received from an ATS provider, before normalization."""

    provider: ATSProvider
    external_id: str
    title: str
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    location: Optional[str] = None
    department: Optional[str] = None
    company: Optional[str] = None
    posted_at: Optional[datetime] = None
    raw_data: dict  # full provider payload for inspection


class NormalizedJob(BaseModel):
    """Common internal schema after normalization (future use)."""

    provider: ATSProvider
    external_id: str
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    company: Optional[str] = None
    posted_at: Optional[datetime] = None


class FetchResult(BaseModel):
    """Result of a single provider fetch operation."""

    provider: ATSProvider
    jobs_fetched: int
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    deactivated: int = 0
    errors: list[str] = []
