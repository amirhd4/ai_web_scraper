from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from worker import AsyncScraperEngine
import httpx
import asyncio
import uuid

scheduler = AsyncIOScheduler()
scraper_engine = AsyncScraperEngine()


async def execute_scheduled_scrape(urls: list, selectors: list, domain: str, ignore_visited: bool, broadcast_func):
    task_id = f"cron-{str(uuid.uuid4())[:8]}"
    async with httpx.AsyncClient(follow_redirects=True, verify=False) as client:
        from schemas import ScrapingTask
        jobs = []
        for url in urls:
            mock_task = ScrapingTask(
                task_id=task_id, url=url, target_domain=domain,
                css_selectors=selectors, ignore_visited=ignore_visited
            )
            jobs.append(scraper_engine.fetch_and_parse(mock_task, client))

        for future in asyncio.as_completed(jobs):
            result = await future
            if result and broadcast_func:
                await broadcast_func({
                    "event": "page_scraped",
                    "task_id": task_id,
                    "url": result.url,
                    "status_code": result.status_code,
                    "data": result.extracted_data,
                    "error": result.error,
                    "is_cron": True
                })


def start_cron_scheduler():
    if not scheduler.running:
        scheduler.start()


def add_scraping_cron(job_id: str, urls: list, selectors: list, domain: str, cron_expr: str, ignore_visited: bool,
                      broadcast_func):
    start_cron_scheduler()
    scheduler.add_job(
        execute_scheduled_scrape,
        CronTrigger.from_crontab(cron_expr),
        id=job_id,
        args=[urls, selectors, domain, ignore_visited, broadcast_func],
        replace_existing=True
    )


def remove_scraping_cron(job_id: str):
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)