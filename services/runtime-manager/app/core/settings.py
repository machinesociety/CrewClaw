from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    runtime_manager_host: str = "0.0.0.0"
    runtime_manager_port: int = 18080
    runtime_public_host: str = "localhost"
    runtime_openclaw_network: str = "clawloops_shared"
    runtime_openclaw_image_ref: str = "ghcr.io/openclaw/openclaw@sha256:d65cc3d5fd0c8b1f752c2f70377843230112250c10e99c3b61769234c217c5db"
    runtime_openclaw_command: str = "node dist/index.js gateway --bind lan --port 18789 --allow-unconfigured"
    runtime_startup_grace_seconds: int = 60
    runtime_startup_poll_seconds: int = 1
    runtime_startup_consecutive_successes: int = 3
    runtime_startup_port: int = 18789

    class Config:
        env_prefix = ""
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
