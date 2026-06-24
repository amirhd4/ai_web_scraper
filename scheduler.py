from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from worker import AsyncScraperEngine
from storage import storage
import httpx
import asyncio
import uuid

scheduler = AsyncIOScheduler()
scraper_engine = AsyncScraperEngine()


async def execute_scheduled_scrape(urls: list, selectors: list, domain: str, broadcast_func):
    """تابعی که در زمان‌های مشخص شده توسط کرون اجرا می‌شود"""
    task_id = f"cron-{str(uuid.uuid4())[:8]}"
    async with httpx.AsyncClient() as client:
        jobs = [scraper_engine.fetch_and_parse(
            type('Task', (), {'task_id': task_id, 'url': url, 'target_domain': domain, 'css_selectors': selectors})(),
            client
        ) for url in urls]

        for future in asyncio.as_completed(jobs):
            result = await future
            if result and broadcast_func:
                await broadcast_func({
                    "event": "page_scraped",
                    "task_id": task_id,
                    "url": result.url,
                    "status_code": result.status_code,
                    "data": result.extracted_data,
                    "is_cron": True
                })


def start_cron_scheduler():
    if not scheduler.running:
        scheduler.start()


def add_scraping_cron(job_id: str, urls: list, selectors: list, domain: str, cron_expr: str, broadcast_func):
    scheduler.add_job(
        execute_scheduled_scrape,
        CronTrigger.from_crontab(cron_expr),
        id=job_id,
        args=[urls, selectors, domain, broadcast_func],
        replace_existing=True
    )


def remove_scraping_cron(job_id: str):
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)