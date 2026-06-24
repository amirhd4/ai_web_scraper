# main.py
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uuid
import httpx
from schemas import ScrapingTask
from worker import AsyncScraperEngine
from storage import storage
import json

app = FastAPI(title="Enterprise Distributed Scraper Control Plane")

# فعال‌سازی CORS برای اتصال راحت فرانت‌اند یا داشبورد مدیریت
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper_engine = AsyncScraperEngine()

# مدیریت کانکشن‌های وب‌ساکت برای مانیتورینگ زنده
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass

manager = ConnectionManager()

async def run_cluster_scraping(task_id: str, urls: list[str], domain: str):
    """مدیریت و اجرای دسته‌ای تسک‌ها به صورت کاملاً غیرهمزمان"""
    async with httpx.AsyncClient() as client:
        jobs = []
        for index, url in enumerate(urls):
            task = ScrapingTask(task_id=task_id, url=url, target_domain=domain)
            jobs.append(scraper_engine.fetch_and_parse(task, client))
            
        # اجرای موازی تمام درخواست‌ها با رعایت ریت‌لیمیت داخلی ورکر
        for future in asyncio.as_completed(jobs):
            result = await future
            if result:
                # ارسال سیگنال زنده به داشبورد مدیریتی وب‌ساکت
                await manager.broadcast({
                    "event": "page_scraped",
                    "task_id": task_id,
                    "url": result.url,
                    "status": "success",
                    "title": result.title
                })

@app.post("/api/v1/scrape/batch")
async def start_batch_scrape(urls: list[str], domain: str, background_tasks: BackgroundTasks):
    """نقطه ورود جاب‌های بزرگ - دریافت لیست کلاینت و سپردن به پس‌زمینه بیدرنگ"""
    task_id = str(uuid.uuid4())
    
    # سپردن کار به Background Tasks جهت آزاد شدن فوری ترافیک API کلاینت
    background_tasks.add_task(run_cluster_scraping, task_id, urls, domain)
    
    return {
        "status": "queued",
        "task_id": task_id,
        "total_urls": len(urls),
        "message": "Scraping cluster initialized in background."
    }

@app.get("/api/v1/scrape/results/{task_id}")
async def get_task_results(task_id: str):
    """دریافت دیتای جمع‌آوری شده یک جاب خاص"""
    data = storage.get_results(task_id)
    return {"task_id": task_id, "count": len(data), "results": data}

@app.websocket("/ws/monitor")
async def websocket_endpoint(websocket: WebSocket):
    """اتصال وب‌ساکت برای رصد لحظه‌ای عملکرد سیستم و مانیتورینگ ورکرها"""
    await manager.connect(websocket)
    try:
        while True:
            # منتظر ماندن برای زنده نگه داشتن کانکشن
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)