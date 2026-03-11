import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("✅ APScheduler started")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)


def add_scheduled_workflow(
    job_id: str,
    workflow: Dict[str, Any],
    interval_type: str,
    interval_value: int,
    execute_fn: Callable
):
    remove_scheduled_workflow(job_id)

    interval_kwargs = {}
    if interval_type == "minute": interval_kwargs["minutes"] = interval_value
    elif interval_type == "hour":  interval_kwargs["hours"]   = interval_value
    elif interval_type == "day":   interval_kwargs["days"]    = interval_value
    elif interval_type == "week":  interval_kwargs["weeks"]   = interval_value
    else: interval_kwargs["minutes"] = 1

    # Wrap async fn so APScheduler can call it correctly
    def sync_wrapper(wf):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(execute_fn(wf))
        else:
            loop.run_until_complete(execute_fn(wf))

    scheduler.add_job(
        sync_wrapper,
        trigger=IntervalTrigger(**interval_kwargs),
        id=job_id,
        args=[workflow],
        replace_existing=True,
        max_instances=1,
        misfire_grace_time=30,
    )
    logger.info(f"✅ Scheduled '{job_id}' every {interval_value} {interval_type}")
    print(f"✅ Scheduled '{job_id}' every {interval_value} {interval_type}")


def remove_scheduled_workflow(job_id: str):
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass


def list_scheduled_jobs() -> list:
    return [
        {
            "id": job.id,
            "next_run": str(job.next_run_time),
            "trigger": str(job.trigger)
        }
        for job in scheduler.get_jobs()
    ]