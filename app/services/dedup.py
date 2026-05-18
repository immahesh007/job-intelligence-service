from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.db import async_session
from app.models.job import RawJob
from app.models.job_orm import Job
from app.services.extractor import extract_seniority, extract_skills


async def upsert_jobs(provider: str, company: str, raw_jobs: list[RawJob]) -> dict:
    """Persist fetched jobs for a single company with dedup on (provider, external_id).

    Only queries/affects rows matching (provider, company), so processing
    one company never touches another company's data.
    """
    if not raw_jobs:
        return {"inserted": 0, "updated": 0, "skipped": 0, "deactivated": 0}

    async with async_session() as session:
        # 1. Load existing keys for this provider + company
        existing = await session.execute(
            select(Job.external_id, Job.posted_at).where(
                Job.provider == provider,
                Job.company == company,
            )
        )
        existing_map: dict[str, datetime | None] = {row[0]: row[1] for row in existing.all()}

        # 2. Split into buckets
        to_upsert: list[dict] = []
        fetched_ids: set[str] = set()

        for job in raw_jobs:
            fetched_ids.add(job.external_id)
            existing_posted = existing_map.get(job.external_id)

            if existing_posted is None:
                to_upsert.append(_job_to_row(provider, job))
            elif job.posted_at and existing_posted and job.posted_at > existing_posted:
                to_upsert.append(_job_to_row(provider, job))

        # 3. UPSERT new + changed
        inserted = 0
        updated = 0
        if to_upsert:
            stmt = insert(Job).values(to_upsert)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_job_provider_external",
                set_={
                    "title": stmt.excluded.title,
                    "description": stmt.excluded.description,
                    "url": stmt.excluded.url,
                    "location": stmt.excluded.location,
                    "department": stmt.excluded.department,
                    "company": stmt.excluded.company,
                    "posted_at": stmt.excluded.posted_at,
                    "skills": stmt.excluded.skills,
                    "seniority_level": stmt.excluded.seniority_level,
                    "raw_data": stmt.excluded.raw_data,
                    "last_seen_at": func_now(),
                    "updated_at": func_now(),
                },
            )
            await session.execute(stmt)
            for row in to_upsert:
                if row["external_id"] not in existing_map:
                    inserted += 1
                else:
                    updated += 1

        # 4. Touch last_seen_at for skipped rows (still present, unchanged)
        skipped = len(raw_jobs) - inserted - updated
        if skipped:
            stale_ids = fetched_ids - {r["external_id"] for r in to_upsert}
            if stale_ids:
                await session.execute(
                    update(Job)
                    .where(Job.provider == provider, Job.company == company, Job.external_id.in_(stale_ids))
                    .values(last_seen_at=func_now())
                )

        # 5. Soft-delete jobs for this company no longer in the feed
        removed_ids = set(existing_map.keys()) - fetched_ids
        deactivated = 0
        if removed_ids:
            result = await session.execute(
                update(Job)
                .where(
                    Job.provider == provider,
                    Job.company == company,
                    Job.external_id.in_(removed_ids),
                    Job.is_active == True,
                )
                .values(is_active=False)
            )
            deactivated = result.rowcount

        await session.commit()

    return {"inserted": inserted, "updated": updated, "skipped": skipped, "deactivated": deactivated}


def _job_to_row(provider: str, job: RawJob) -> dict:
    return {
        "provider": provider,
        "external_id": job.external_id,
        "title": job.title,
        "description": job.description,
        "url": str(job.url) if job.url else None,
        "location": job.location,
        "department": job.department,
        "company": job.company,
        "posted_at": job.posted_at,
        "skills": extract_skills(job.title, job.description) or None,
        "seniority_level": extract_seniority(job.title, job.description),
        "raw_data": job.raw_data,
        "is_active": True,
    }


def func_now():
    return datetime.now(timezone.utc)
