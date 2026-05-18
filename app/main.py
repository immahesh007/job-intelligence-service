from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import engine
from app.models.job_orm import Base
from app.routers import jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="Job Intelligence Service",
    description="ATS job aggregation and intelligence API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(jobs.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
