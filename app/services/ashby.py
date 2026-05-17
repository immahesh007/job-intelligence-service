from typing import Optional

import httpx

from app.models.job import ATSProvider, RawJob


ASHBY_BOARD_URL = "https://api.ashbyhq.com/posting-api/job-board/{company}"


async def fetch_ashby_jobs(company: str, client: Optional[httpx.AsyncClient] = None) -> list[RawJob]:
    """Fetch jobs from Ashby's public job board API."""
    url = ASHBY_BOARD_URL.format(company=company)
    async with client or httpx.AsyncClient() as c:
        resp = await c.get(url)
        resp.raise_for_status()
        data = resp.json()

    jobs: list[RawJob] = []
    for item in data.get("jobs", []):
        jobs.append(
            RawJob(
                provider=ATSProvider.ASHBY,
                external_id=item["id"],
                title=item["title"],
                description=item.get("descriptionPlain"),
                url=item.get("jobUrl"),
                location=item.get("location"),
                department=item.get("department"),
                company=data.get("board", {}).get("companyName", company) if isinstance(data.get("board"), dict) else company,
                posted_at=item.get("publishedAt"),
                raw_data=item,
            )
        )
    return jobs
