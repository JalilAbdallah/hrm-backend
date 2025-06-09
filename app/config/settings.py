from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URL: str
    DATABASE_NAME: str
    JWT_SECRET: str
    JWT_EXPIRATION: str = "1h"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
settings = Settings()