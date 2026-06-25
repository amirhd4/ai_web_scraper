import asyncio
from typing import Optional
import httpx
from bs4 import BeautifulSoup
from schemas import ScrapingTask, ScrapedDataPayload
from storage import storage
from config import settings
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ScraperWorker")

class AsyncScraperEngine:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    async def _extract_with_ai(self, html_content: str, user_prompt: str, client: httpx.AsyncClient) -> dict:
        """استخراج اطلاعات با استفاده از ساختار داده هوشمند گوگل جمینی"""
        soup = BeautifulSoup(html_content, 'html.parser')
        # حذف تگ‌های اسکریپت و استایل برای کاهش حجم توکن مصرفی و صرفه‌جویی هزینه
        for script in soup(["script", "style"]):
            script.extract()
        page_text = soup.get_text(separator="\n", strip=True)[:16000] # محدودسازی متن برای بهینه‌سازی سرعت

        system_instruction = (
            "You are an expert data scraper. Extract the requested data from the provided web page text "
            "based on the user's prompt. You MUST return a valid JSON object representing the extracted data."
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": f"User Request: {user_prompt}\n\nWeb Page Content:\n{page_text}"}
                ]
            }],
            "systemInstruction": {
                "parts": [{"text": system_instruction}]
            },
            "generationConfig": {
                "responseMimeType": "application/json" # تضمین دریافت خروجی معتبر JSON
            }
        }

        try:
            response = await client.post(url, json=payload, timeout=20.0)
            if response.status_code == 200:
                res_json = response.json()
                raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
                return json.loads(raw_text)
            else:
                return {"error": f"AI Gateway returned status {response.status_code}"}
        except Exception as e:
            return {"error": f"AI Parsing exception: {str(e)}"}

    async def fetch_and_parse(self, task: ScrapingTask, client: httpx.AsyncClient) -> ScrapedDataPayload:
        url_str = str(task.url)

        if not task.ignore_visited and storage.is_visited(url_str):
            logger.info(f"URL already visited, skipping asset: {url_str}")
            return ScrapedDataPayload(
                url=url_str, status_code=None, extracted_data={},
                error="این آدرس قبلاً دیده شده است. برای بروزرسانی، گزینه 'اسکرپ مجدد دیتای تکراری' را فعال کنید."
            )

        async with self.semaphore:
            try:
                logger.info(f"Scraping Engine Execution: {url_str} via {task.extraction_mode} mode")
                response = await client.get(url_str, headers=self.headers, timeout=settings.DEFAULT_TIMEOUT, follow_redirects=True)
                storage.mark_as_visited(url_str)

                dynamic_extracted_data = {}

                if task.extraction_mode == "ai":
                    dynamic_extracted_data = await self._extract_with_ai(response.text, task.ai_prompt, client)
                else:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for selector in task.css_selectors:
                        clean_selector = selector.strip()
                        if not clean_selector: continue
                        elements = soup.select(clean_selector)
                        dynamic_extracted_data[clean_selector] = [el.get_text(strip=True) for el in elements] if elements else []

                payload = ScrapedDataPayload(
                    url=url_str,
                    status_code=response.status_code,
                    extracted_data=dynamic_extracted_data
                )

                storage.save_result(task.task_id, payload.model_dump(mode='json'))
                return payload

            except httpx.HTTPError as e:
                logger.error(f"Network failure for {url_str}: {str(e)}")
                return ScrapedDataPayload(url=url_str, status_code=None, extracted_data={}, error=f"خطای شبکه: {str(e)}")
            except Exception as e:
                logger.error(f"Engine parsing failure for {url_str}: {str(e)}")
                return ScrapedDataPayload(url=url_str, status_code=None, extracted_data={}, error=f"خطای ساختاری: {str(e)}")