import asyncio
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from schemas import ScrapingTask, ScrapedDataPayload
from storage import storage
from config import settings
import logging
import json

from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScraperWorker")


class AsyncScraperEngine:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.ai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def _extract_with_ai(self, html_content: str, user_prompt: str) -> dict:
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        page_text = soup.get_text(separator="\n", strip=True)[:18000]

        system_instruction_text = (
            "You are an expert data scraper. Extract the requested data from the provided web page text "
            "based on the user's prompt. You MUST return a valid JSON object representing the extracted data."
        )

        # آماده‌سازی ساختار کانفیگ جدید به صورت کاملاً Type-safe و بومی
        config = types.GenerateContentConfig(
            system_instruction=system_instruction_text,
            response_mime_type="application/json"
        )

        try:
            def call_gemini():
                return self.ai_client.models.generate_content(
                    model="gemini-3.5-flash",
                    contents=f"User Request: {user_prompt}\n\nWeb Page Content:\n{page_text}",
                    config=config
                )

            # سپردن اجرای تابع سینک به تردپول آسنکرون
            response = await asyncio.to_thread(call_gemini)

            if response.text:
                return json.loads(response.text)
            else:
                return {"error": "مدل پاسخ خالی برگرداند."}

        except Exception as e:
            logger.error(f"Gemini SDK Execution error: {str(e)}")
            return {"error": f"AI Parsing error: {str(e)}"}

    async def fetch_and_parse(self, task: ScrapingTask, client: httpx.AsyncClient) -> ScrapedDataPayload:
        url_str = str(task.url)

        if not task.ignore_visited and storage.is_visited(url_str):
            logger.info(f"URL already visited, skipping asset: {url_str}")
            return ScrapedDataPayload(
                url=url_str, status_code=None, extracted_data={},
                error="این آدرس قبلاً دیده شده است. برای بروزرسانی، گزینه نادیده گرفتن تاریخچه را فعال کنید."
            )

        async with self.semaphore:
            try:
                logger.info(f"Scraping Engine executing: {url_str} via [{task.extraction_mode}]")
                response = await client.get(url_str, headers=self.headers, timeout=settings.DEFAULT_TIMEOUT,
                                            follow_redirects=True)
                storage.mark_as_visited(url_str)

                dynamic_extracted_data = {}

                if task.extraction_mode == "ai":
                    dynamic_extracted_data = await self._extract_with_ai(response.text, task.ai_prompt)
                else:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for selector in task.css_selectors:
                        clean_selector = selector.strip()
                        if not clean_selector: continue
                        elements = soup.select(clean_selector)
                        dynamic_extracted_data[clean_selector] = [el.get_text(strip=True) for el in
                                                                  elements] if elements else []

                return ScrapedDataPayload(url=url_str, status_code=response.status_code,
                                          extracted_data=dynamic_extracted_data)

            except httpx.HTTPError as e:
                return ScrapedDataPayload(url=url_str, status_code=None, extracted_data={},
                                          error=f"خطای شبکه: {str(e)}")
            except Exception as e:
                return ScrapedDataPayload(url=url_str, status_code=None, extracted_data={},
                                          error=f"خطای داخلی ورکر: {str(e)}")