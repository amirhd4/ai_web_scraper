from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class ExtractionMode(str, Enum):
    CSS = "css"
    AI = "ai"

class InstantJobCreate(BaseModel):
    urls: List[HttpUrl]
    domain: str
    ignore_visited: bool = False
    extraction_mode: ExtractionMode = Field(default=ExtractionMode.CSS)
    css_selectors: Optional[List[str]] = Field(default_factory=list)
    ai_prompt: Optional[str] = None

class CronJobCreate(BaseModel):
    urls: List[HttpUrl]
    domain: str
    cron_expression: str
    ignore_visited: bool = False
    extraction_mode: ExtractionMode = Field(default=ExtractionMode.CSS)
    css_selectors: Optional[List[str]] = Field(default_factory=list)
    ai_prompt: Optional[str] = None

class ScrapingTask(BaseModel):
    task_id: str
    url: HttpUrl
    target_domain: str
    ignore_visited: bool = False
    extraction_mode: ExtractionMode
    css_selectors: List[str]
    ai_prompt: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ScrapedDataPayload(BaseModel):
    url: str
    status_code: Optional[int] = None
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    scraped_at: datetime = Field(default_factory=datetime.utcnow)