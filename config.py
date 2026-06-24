from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Distributed Intelligence Scraper"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    DEFAULT_TIMEOUT: int = 10
    MAX_CONCURRENT_REQUESTS: int = 5
    
    class Config:
        env_file = ".env"

settings = Settings()