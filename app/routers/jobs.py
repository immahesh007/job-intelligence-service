import asyncio
import json
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.config import load_companies
from app.models.job import ATSProvider, FetchResult, RawJob
from app.services.ashby import fetch_ashby_jobs
from app.services.dedup import upsert_jobs
from app.services.greenhouse import fetch_greenhouse_jobs
from app.services.lever import fetch_lever_jobs

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

TEST_DIR = Path(__file__).resolve().parent.parent.parent / "test"

PROVIDER_REGISTRY: list[tuple[ATSProvider, Callable]] = [
    (ATSProvider.GREENHOUSE, fetch_greenhouse_jobs),
    (ATSProvider.LEVER, fetch_lever_jobs),
    (ATSProvider.ASHBY, fetch_ashby_jobs),
]


def _resolve_companies(provider: ATSProvider, override: Optional[str]) -> list[str]:
    """Return companies from the file, optionally adding/replacing with a query-param override."""
    slugs = load_companies(provider)
    if override:
        slugs = [s for s in slugs if s != override]
        slugs.append(override)  # ensure the override is included
    return slugs


@router.post("/fetch", response_model=list[FetchResult])
async def trigger_job_fetch(
    greenhouse_company: Optional[str] = Query(None, description="Override/add a Greenhouse company slug"),
    lever_company: Optional[str] = Query(None, description="Override/add a Lever company slug"),
    ashby_company: Optional[str] = Query(None, description="Override/add an Ashby company slug"),
):
    """Fetch jobs for all companies listed in companies/*.txt and persist with dedup.

    Optional query params let you add or override a company for a one-off run.
    """

    async def fetch_and_persist(provider: ATSProvider, fetcher: Callable, company: str):
        raw_jobs: list[RawJob] = await fetcher(company)
        counts = await upsert_jobs(provider.value, company, raw_jobs)
        return provider, company, len(raw_jobs), counts, None

    async def safe_fetch(provider: ATSProvider, fetcher: Callable, company: str):
        try:
            return await fetch_and_persist(provider, fetcher, company)
        except Exception as e:
            return provider, company, 0, {}, str(e)

    tasks = []
    for provider, fetcher in PROVIDER_REGISTRY:
        companies = _resolve_companies(provider, {
            ATSProvider.GREENHOUSE: greenhouse_company,
            ATSProvider.LEVER: lever_company,
            ATSProvider.ASHBY: ashby_company,
        }[provider])
        for company in companies:
            tasks.append(safe_fetch(provider, fetcher, company))

    if not tasks:
        raise HTTPException(status_code=400, detail="No companies configured.")

    results_raw = await asyncio.gather(*tasks)

    results: list[FetchResult] = []
    for provider, company, fetched, counts, error in results_raw:
        if error:
            results.append(FetchResult(provider=provider, jobs_fetched=0, errors=[f"{company}: {error}"]))
        else:
            results.append(FetchResult(
                provider=provider,
                jobs_fetched=fetched,
                inserted=counts.get("inserted", 0),
                updated=counts.get("updated", 0),
                skipped=counts.get("skipped", 0),
                deactivated=counts.get("deactivated", 0),
            ))
    return results


@router.post("/debug/sample")
async def save_sample_jobs(
    greenhouse_company: Optional[str] = Query(None),
    lever_company: Optional[str] = Query(None),
    ashby_company: Optional[str] = Query(None),
    limit: int = Query(5, ge=1, le=20, description="Max records per company to save"),
):
    """Debug API: fetch jobs for configured companies and save samples to test/."""
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    saved: dict[str, dict] = {}

    for provider, fetcher in PROVIDER_REGISTRY:
        override = {
            ATSProvider.GREENHOUSE: greenhouse_company,
            ATSProvider.LEVER: lever_company,
            ATSProvider.ASHBY: ashby_company,
        }[provider]
        companies = _resolve_companies(provider, override)
        for company in companies:
            key = f"{provider.value}/{company}"
            try:
                jobs: list[RawJob] = await fetcher(company)
                sample = [job.model_dump(mode="json") for job in jobs[:limit]]
                out_path = TEST_DIR / f"{provider.value}_{company}_sample.json"
                out_path.write_text(json.dumps(sample, indent=2, default=str))
                saved[key] = {"file": str(out_path), "records_saved": len(sample), "total_available": len(jobs)}
            except Exception as e:
                saved[key] = {"error": str(e)}

    if not saved:
        raise HTTPException(status_code=400, detail="No companies configured.")

    return {
        "message": "Sample data saved",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "providers": saved,
    }
