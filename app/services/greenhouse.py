from typing import Optional

import httpx

from app.models.job import ATSProvider, RawJob


GREENHOUSE_BOARDS_URL = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs"


async def fetch_greenhouse_jobs(company: str, client: Optional[httpx.AsyncClient] = None) -> list[RawJob]:
    """Fetch jobs from Greenhouse's public board API."""
    url = GREENHOUSE_BOARDS_URL.format(company=company)
    async with client or httpx.AsyncClient() as c:
        resp = await c.get(url)
        resp.raise_for_status()
        data = resp.json()

    jobs: list[RawJob] = []
    for item in data.get("jobs", []):
        jobs.append(
            RawJob(
                provider=ATSProvider.GREENHOUSE,
                external_id=str(item["id"]),
                title=item["title"],
                description=item.get("metadata", [{}])[0].get("description") if item.get("metadata") else None,
                url=item.get("absolute_url"),
                location=item.get("location", {}).get("name"),
                department=item.get("departments", [{}])[0].get("name") if item.get("departments") else None,
                company=data.get("name", company),
                posted_at=item.get("updated_at"),
                raw_data=item,
            )
        )
    return jobs
