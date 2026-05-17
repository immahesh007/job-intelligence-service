import logging
from typing import Optional

import httpx
from sqlalchemy import select

from app.db import async_session
from app.models.job import ATSProvider, RawJob
from app.models.job_orm import Job
from app.services.cleaner import html_to_text

logger = logging.getLogger(__name__)

GREENHOUSE_BOARDS_URL = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
GREENHOUSE_JOB_URL = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs/{job_id}"


async def fetch_greenhouse_jobs(company: str, client: Optional[httpx.AsyncClient] = None) -> list[RawJob]:
    """Fetch jobs from the Greenhouse board API.

    For jobs not already in the DB, the per-job detail endpoint is called
    to extract the full description.  Existing jobs skip the extra call.
    """
    async with client or httpx.AsyncClient() as c:
        # 1. Fetch board list
        board_url = GREENHOUSE_BOARDS_URL.format(company=company)
        resp = await c.get(board_url)
        resp.raise_for_status()
        data = resp.json()
        board_name = data.get("name", company)
        items = data.get("jobs", [])

        # 2. Which jobs are new?  Query the DB once.
        existing_ids: set[str] = set()
        async with async_session() as session:
            rows = await session.execute(
                select(Job.external_id).where(
                    Job.provider == ATSProvider.GREENHOUSE.value,
                    Job.company == company,
                )
            )
            existing_ids = {row[0] for row in rows.all()}

        # 3. Build RawJob objects — fetch detail only for new jobs
        jobs: list[RawJob] = []
        for item in items:
            external_id = str(item["id"])
            description: Optional[str] = None

            if external_id not in existing_ids:
                description = await _fetch_detail(c, company, external_id)

            jobs.append(
                RawJob(
                    provider=ATSProvider.GREENHOUSE,
                    external_id=external_id,
                    title=item["title"],
                    description=description,
                    url=item.get("absolute_url"),
                    location=item.get("location", {}).get("name"),
                    department=item.get("departments", [{}])[0].get("name") if item.get("departments") else None,
                    company=board_name,
                    posted_at=item.get("updated_at"),
                    raw_data=item,
                )
            )

    return jobs


async def _fetch_detail(c: httpx.AsyncClient, company: str, job_id: str) -> Optional[str]:
    """Fetch and clean the description from a single job detail endpoint."""
    try:
        detail_url = GREENHOUSE_JOB_URL.format(company=company, job_id=job_id)
        resp = await c.get(detail_url)
        resp.raise_for_status()
        content = resp.json().get("content")
        if content:
            return html_to_text(content)
    except Exception:
        logger.warning("Failed to fetch detail for greenhouse job %s/%s", company, job_id)
    return None
