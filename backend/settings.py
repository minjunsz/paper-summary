from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openrouter_api_key: str = ""

    @field_validator("openrouter_api_key", mode="before")
    @classmethod
    def check_api_key(cls, v: str) -> str:
        if not v:
            raise ValueError("openrouter_api_key must be set in environment")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
