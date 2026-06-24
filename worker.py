# worker.py
import asyncio
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from schemas import ScrapingTask, ScrapedDataPayload
from storage import storage
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScraperWorker")

class AsyncScraperEngine:
    def __init__(self):
        # کنترل نرخ درخواست‌های همزمان برای جلوگیری از بن شدن
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def fetch_and_parse(self, task: ScrapingTask, client: httpx.AsyncClient) -> Optional[ScrapedDataPayload]:
        url_str = str(task.url)
        
        if storage.is_visited(url_str):
            logger.info(f"URL already visited, skipping: {url_str}")
            return None

        async with self.semaphore:
            try:
                logger.info(f"Scraping: {url_str}")
                response = await client.get(url_str, headers=self.headers, timeout=settings.DEFAULT_TIMEOUT)
                
                storage.mark_as_visited(url_str)
                
                # یک پارسر نمونه: استخراج تایتل و تگ‌های H1
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.string if soup.title else "No Title"
                h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]
                
                payload = ScrapedDataPayload(
                    url=url_str,
                    status_code=response.status_code,
                    title=title,
                    extracted_data={"h1_contents": h1_tags}
                )
                
                # ذخیره در دیتابیس موقت ردیس
                storage.save_result(task.task_id, payload.model_dump())
                return payload
                
            except httpx.HTTPError as e:
                logger.error(f"Network error fetching {url_str}: {str(e)}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error parsing {url_str}: {str(e)}")
                return None