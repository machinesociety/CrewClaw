from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    runtime_manager_host: str = "0.0.0.0"
    runtime_manager_port: int = 18080
    runtime_public_host: str = "localhost"
    runtime_openclaw_network: str = "clawloops_shared"
    runtime_openclaw_image_ref: str = (
        "ghcr.io/openclaw/openclaw@sha256:0b2170d5ec3a487a6313ed0556d377c5c5c80a0f806043daa2e685a4bedd45e3"
    )
    runtime_openclaw_command: str = "node dist/index.js gateway --bind lan --port 18789"
    runtime_startup_grace_seconds: int = 30
    runtime_startup_poll_seconds: int = 1
    runtime_startup_consecutive_successes: int = 3
    runtime_startup_port: int = 18789

    class Config:
        env_prefix = ""
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
