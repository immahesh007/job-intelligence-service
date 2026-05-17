from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler()


def configure_scheduler(fetch_callback):
    """Register the 6 AM daily job and start the scheduler.

    The scheduler runs in the same process for simplicity. In production
    this should be replaced with Celery Beat workers.
    """
    scheduler.add_job(
        fetch_callback,
        trigger=CronTrigger(hour=6, minute=0),
        id="daily_job_fetch",
        name="Daily 6 AM job fetch from all ATS providers",
        replace_existing=True,
    )
    scheduler.start()
