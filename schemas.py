from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone


class ScrapingTask(BaseModel):
    task_id: str
    url: HttpUrl
    target_domain: str
    depth: int = Field(default=1, ge=1, le=5)
    created_at: datetime = Field(default_factory=datetime.now)
    css_selectors: List[str] = Field(default_factory=lambda: ["title", "h1"])


class ScrapedDataPayload(BaseModel):
    url: str
    status_code: int
    title: Optional[str] = None
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    scraped_at: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None  # فیلد جدید برای استریم خطا به UI


class InstantJobCreate(BaseModel):
    urls: List[HttpUrl]
    selectors: List[str]
    domain: str
    cron_expression: str


class CronJobCreate(BaseModel):
    urls: List[HttpUrl]
    selectors: List[str]
    domain: str
    cron_expression: str = Field(..., description="استاندارد کرون جاب مثل: */1 * * * *")