"""
APScheduler service — runs as its own container.

Add scheduled jobs to register_jobs(). Each job should:
    - Log start, success, and failures (db_logger writes ERRORs to app_logs)
    - Be idempotent if possible (jobs may run twice if the container restarts mid-run)
    - Wrap heavy work in try/except so one failing job doesn't kill the scheduler

Disabled by default in test env via SCHEDULER_ENABLED=false.
"""

import asyncio
import logging
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from api.config import settings
from api.utils.db_logger import install_db_logger


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)
install_db_logger(service="scheduler")


async def example_daily_job() -> None:
    """Replace with real job logic. Always log start + outcome."""
    logger.info("example_daily_job: starting")
    try:
        # Real work goes here. Open an AsyncSessionLocal() if you need DB access.
        logger.info("example_daily_job: completed")
    except Exception as exc:
        logger.error("example_daily_job: failed — %s", str(exc), exc_info=True)


def register_jobs(scheduler: AsyncIOScheduler) -> None:
    """All cron registrations live here so they're easy to find and audit."""
    scheduler.add_job(
        example_daily_job,
        CronTrigger(hour=7, minute=0),
        id="example_daily",
        replace_existing=True,
    )


async def run_scheduler() -> None:
    scheduler = AsyncIOScheduler(timezone="Europe/Stockholm")
    register_jobs(scheduler)
    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))

    try:
        # Idle forever — APScheduler runs jobs in the background.
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped")


def main() -> None:
    if not settings.scheduler_enabled:
        logger.info("Scheduler disabled (SCHEDULER_ENABLED=false) — idling")
        while True:
            time.sleep(3600)
    asyncio.run(run_scheduler())


if __name__ == "__main__":
    main()
