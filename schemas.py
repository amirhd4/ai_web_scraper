from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class ScrapingTask(BaseModel):
    task_id: str
    url: HttpUrl
    target_domain: str
    css_selectors: List[str]
    ignore_visited: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ScrapedDataPayload(BaseModel):
    url: str
    status_code: Optional[int] = None
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)

class CronJobCreate(BaseModel):
    urls: List[HttpUrl]
    selectors: List[str]
    domain: str
    cron_expression: str
    ignore_visited: bool = False

class InstantJobCreate(BaseModel):
    urls: List[HttpUrl]
    selectors: List[str]
    domain: str
    ignore_visited: bool = False