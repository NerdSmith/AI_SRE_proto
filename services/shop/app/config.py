import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    version: str = os.getenv("APP_VERSION", "2.3.1")
    previous_version: str = os.getenv("PREVIOUS_VERSION", "2.3.1")
    payment_timeout_ms: int = int(os.getenv("PAYMENT_TIMEOUT_MS", "1000"))
    pool_size: int = int(os.getenv("POOL_SIZE", "5"))
    pool_wait_ms: int = int(os.getenv("POOL_WAIT_MS", "200"))


settings = Settings()
