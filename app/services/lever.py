from typing import Optional

import httpx

from app.models.job import ATSProvider, RawJob


LEVER_POSTINGS_URL = "https://api.lever.co/v0/postings/{company}"


async def fetch_lever_jobs(company: str, client: Optional[httpx.AsyncClient] = None) -> list[RawJob]:
    """Fetch jobs from Lever's public postings API."""
    url = LEVER_POSTINGS_URL.format(company=company)
    async with client or httpx.AsyncClient() as c:
        resp = await c.get(url)
        resp.raise_for_status()
        data = resp.json()

    jobs: list[RawJob] = []
    for item in data:
        jobs.append(
            RawJob(
                provider=ATSProvider.LEVER,
                external_id=item["id"],
                title=item["text"],
                description=item.get("descriptionPlain"),
                url=item.get("hostedUrl"),
                location=item.get("categories", {}).get("location"),
                department=item.get("categories", {}).get("team"),
                company=company,
                posted_at=item.get("createdAt"),
                raw_data=item,
            )
        )
    return jobs
