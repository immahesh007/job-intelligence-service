from pathlib import Path

from dotenv import load_dotenv

# Load .env before any other imports that read environment variables
load_dotenv(Path(__file__).resolve().parent / ".env")

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import load_companies
from app.db import engine
from app.models.job import ATSProvider
from app.models.job_orm import Base
from app.routers import jobs, matching
from app.scheduler import configure_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    configure_scheduler(_daily_fetch)
    yield


app = FastAPI(
    title="Job Intelligence Service",
    description="ATS job aggregation and intelligence API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(jobs.router)
app.include_router(matching.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


async def _daily_fetch():
    """Callback for the 6 AM scheduler — fetches jobs from all configured companies."""
    from app.services.ashby import fetch_ashby_jobs
    from app.services.dedup import upsert_jobs
    from app.services.greenhouse import fetch_greenhouse_jobs
    from app.services.lever import fetch_lever_jobs

    registry = [
        (ATSProvider.GREENHOUSE, fetch_greenhouse_jobs),
        (ATSProvider.LEVER, fetch_lever_jobs),
        (ATSProvider.ASHBY, fetch_ashby_jobs),
    ]
    for provider, fetcher in registry:
        for company in load_companies(provider):
            try:
                raw_jobs = await fetcher(company)
                await upsert_jobs(provider.value, company, raw_jobs)
            except Exception:
                pass  # log in production, one failure shouldn't block others
