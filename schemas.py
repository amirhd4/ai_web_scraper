# schemas.py
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ScrapingTask(BaseModel):
    task_id: str
    url: HttpUrl
    target_domain: str
    depth: int = Field(default=1, ge=1, le=5)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ScrapedDataPayload(BaseModel):
    url: str
    status_code: int
    title: Optional[str] = None
    extracted_data: Dict[str, Any]
    scraped_at: datetime = Field(default_factory=datetime.utcnow)