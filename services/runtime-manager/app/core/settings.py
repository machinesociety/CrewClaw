from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    runtime_manager_host: str = "0.0.0.0"
    runtime_manager_port: int = 18080
    runtime_public_host: str = "localhost"
    runtime_openclaw_network: str = "clawloops_shared"
    runtime_user_files_mount_dir: str = "/var/lib/clawloops/user-files"
    runtime_public_files_mount_dir: str = "/var/lib/clawloops/public-area"
    runtime_user_files_host_path: str | None = None
    runtime_openclaw_image_ref: str = "ghcr.io/openclaw/openclaw@sha256:7ea070b04d1e70811fe8ba15feaad5890b1646021b24e00f4795bd4587a594ed"
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

