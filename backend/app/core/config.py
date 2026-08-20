"""Application configuration, loaded from environment variables.

Secrets (Supabase service key, JWT secret) live ONLY in the backend env and are
never shipped to the client. See docs/03-lld.md §7.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_name: str = "Mingle"
    environment: str = "dev"  # dev | prod

    # --- Supabase (DB + Auth) ---
    supabase_url: str = ""  # e.g. https://xxxx.supabase.co
    supabase_service_key: str = ""  # service role key, server-side only
    supabase_jwt_secret: str = ""  # for verifying Supabase-issued JWTs (HS256)

    # --- CORS: comma-separated list of allowed frontend origins ---
    cors_origins: str = "http://localhost:5173"

    # --- Public base URL of the frontend (used to build invite/result links) ---
    frontend_base_url: str = "http://localhost:5173"

    # --- Anti-abuse ---
    # Absolute server-side ceiling on responses per catch-up. A creator may set a
    # lower limit, but never a higher one, this caps DB pollution from bots.
    response_hard_cap: int = 200

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
