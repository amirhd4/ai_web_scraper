import redis
from config import settings
import json

class RedisManager:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT, 
            decode_responses=True
        )
    
    def is_visited(self, url: str) -> bool:
        """بررسی تکراری بودن URL در کسری از میلی‌ثانیه"""
        return self.client.sismember("scraped_urls", url)
    
    def mark_as_visited(self, url: str):
        """علامت‌گذاری URL به عنوان دیده شده"""
        self.client.sadd("scraped_urls", url)
        
    def save_result(self, task_id: str, data: dict):
        """ذخیره موقت دیتای استخراج شده در ردیس برای لوله خروجی"""
        self.client.rpush(f"results:{task_id}", json.dumps(data))
        
    def get_results(self, task_id: str):
        results = self.client.lrange(f"results:{task_id}", 0, -1)
        return [json.loads(r) for r in results]

storage = RedisManager()