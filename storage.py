import redis
from config import settings
import json


class RedisManager:
    def __init__(self):
        self.client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True)

    def is_visited(self, url: str) -> bool:
        return self.client.sismember("scraped_urls", url)

    def mark_as_visited(self, url: str):
        self.client.sadd("scraped_urls", url)

    def save_result(self, task_id: str, data: dict):
        self.client.rpush(f"results:{task_id}", json.dumps(data))

    def get_results(self, task_id: str):
        results = self.client.lrange(f"results:{task_id}", 0, -1)
        return [json.loads(r) for r in results]

    def save_cron_job(self, job_id: str, job_data: dict):
        self.client.hset("active_cron_jobs", job_id, json.dumps(job_data))

    def get_all_cron_jobs(self):
        jobs = self.client.hgetall("active_cron_jobs")
        return {k: json.loads(v) for k, v in jobs.items()}

    def delete_cron_job(self, job_id: str):
        self.client.hdel("active_cron_jobs", job_id)


storage = RedisManager()