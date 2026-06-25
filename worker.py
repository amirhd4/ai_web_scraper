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
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def fetch_and_parse(self, task: ScrapingTask, client: httpx.AsyncClient) -> ScrapedDataPayload:
        url_str = str(task.url)

        if storage.is_visited(url_str):
            logger.info(f"URL already visited: {url_str}")
            return ScrapedDataPayload(url=url_str, error="این آدرس قبلاً اسکرپ شده است (Visited)")

        async with self.semaphore:
            try:
                logger.info(f"Scraping Engine testing: {url_str}")
                # اضافه کردن قابلیت تعقیب ریدایرکت‌ها برای جلوگیری از خطای ۳۰۱ گوگل
                response = await client.get(url_str, headers=self.headers, timeout=settings.DEFAULT_TIMEOUT,
                                            follow_redirects=True)

                storage.mark_as_visited(url_str)
                soup = BeautifulSoup(response.text, 'html.parser')

                dynamic_extracted_data = {}
                for selector in task.css_selectors:
                    clean_selector = selector.strip()
                    if not clean_selector:
                        continue

                    elements = soup.select(clean_selector)
                    dynamic_extracted_data[clean_selector] = [el.get_text(strip=True) for el in
                                                              elements] if elements else []

                payload = ScrapedDataPayload(
                    url=url_str,
                    status_code=response.status_code,
                    extracted_data=dynamic_extracted_data
                )

                storage.save_result(task.task_id, payload.model_dump(mode='json'))
                return payload

            except httpx.HTTPError as e:
                logger.error(f"Network failure for {url_str}: {str(e)}")
                return ScrapedDataPayload(url=url_str, error=f"خطای شبکه: {str(e)}")
            except Exception as e:
                logger.error(f"Engine parsing failure for {url_str}: {str(e)}")
                return ScrapedDataPayload(url=url_str, error=f"خطای ساختاری: {str(e)}")