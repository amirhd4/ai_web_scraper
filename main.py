from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import uuid
import httpx
import asyncio
import json
from schemas import ScrapingTask, CronJobCreate, InstantJobCreate
from worker import AsyncScraperEngine
from storage import storage
from scheduler import start_cron_scheduler, add_scraping_cron, remove_scraping_cron


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_cron_scheduler()
    yield


app = FastAPI(title="Enterprise Control Center", lifespan=lifespan)


class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass


manager = ConnectionManager()
scraper_engine = AsyncScraperEngine()


async def run_cluster_scraping(task_id: str, urls: list[str], selectors: list[str], domain: str, ignore_visited: bool):
    async with httpx.AsyncClient(follow_redirects=True, verify=False) as client:
        jobs = [scraper_engine.fetch_and_parse(
            ScrapingTask(task_id=task_id, url=url, target_domain=domain, css_selectors=selectors,
                         ignore_visited=ignore_visited), client
        ) for url in urls]
        for future in asyncio.as_completed(jobs):
            result = await future
            if result:
                await manager.broadcast({
                    "event": "page_scraped", "task_id": task_id, "url": result.url,
                    "status_code": result.status_code, "data": result.extracted_data,
                    "error": result.error, "is_cron": False
                })


@app.post("/api/v1/scrape/batch")
async def start_batch_scrape(payload: InstantJobCreate, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]
    urls_str = [str(u) for u in payload.urls]
    background_tasks.add_task(run_cluster_scraping, task_id, urls_str, payload.selectors, payload.domain,
                              payload.ignore_visited)
    return {"status": "queued", "task_id": task_id}


@app.post("/api/v1/cron")
async def create_cron_task(payload: CronJobCreate):
    job_id = f"cron-job-{str(uuid.uuid4())[:6]}"
    urls_str = [str(u) for u in payload.urls]
    try:
        add_scraping_cron(job_id, urls_str, payload.selectors, payload.domain, payload.cron_expression,
                          payload.ignore_visited, manager.broadcast)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Cron Expression: {str(e)}")

    storage.save_cron_job(job_id, {
        "job_id": job_id, "urls": urls_str, "selectors": payload.selectors,
        "domain": payload.domain, "cron": payload.cron_expression, "ignore_visited": payload.ignore_visited
    })
    return {"status": "cron_scheduled", "job_id": job_id}


@app.get("/api/v1/cron")
async def list_cron_tasks():
    return storage.get_all_cron_jobs()


@app.delete("/api/v1/cron/{job_id}")
async def delete_cron_task(job_id: str):
    remove_scraping_cron(job_id)
    storage.delete_cron_job(job_id)
    return {"status": "deleted", "job_id": job_id}


@app.websocket("/ws/monitor")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/static/index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)